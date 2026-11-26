# -*- coding: utf-8 -*-
"""ETL 引擎（L1）—— 按配方清洗系统导出的大文件，产出周报数据与看板子集。

设计要点（详见 docs/周报月报自动化方案.md 第 3、8 章）：
* **只用标准库**：公司内网不能 pip install，Python 3.10 开箱可跑。
* **流式读 xlsx**：按 <row> 逐行解析、立即 clear，1.4GB 的 sheet XML 不会整串进内存。
* **单遍扫描 + 临时 spool**：一遍算出订单级指标并把原始行落到临时 CSV，
  再按"值得看的单"过滤成明细子集（避免为了取明细再解析一遍 XML）。
* **口径全部来自配方**（recipes/*.json），代码里不写死阈值。

用法：
    py etl_engine.py --input 放行导出_2026W48.xlsx --recipe recipes/weekly_overtime.json
    py etl_engine.py --input xxx.csv --recipe ... --batch 2026W48 --out out

产物（默认 out/<批次>/）：
    01_KPI.csv          一行，周报抬头数字
    02..0N_<维度>.csv   按配方里的 dimensions 逐个输出
    09_时长分档.csv      超时时长四档分布
    09_明细_超时单.csv   只留超时/未结案的单（40 列原样）→ 直接拖进看板
    summary.json        结构化汇总（给 Dify 写分析文字 / 模板填充用）
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# 字段别名（繁简混排的导出表头 → 标准名）。新增来源只往这里加，代码不动。
FIELD_ALIASES = {
    "申請日期": ["申請日期", "申请日期", "申請时间", "申请时间"],
    "放行單號": ["放行單號", "放行单号", "單號", "单号"],
    "物品類型": ["物品類型", "物品类型"],
    "物品分類": ["物品分類", "物品分类"],
    "申請人姓名": ["申請人姓名", "申请人姓名"],
    "申請人部門": ["申請人部門", "申请人部门", "申請部門", "申请部门"],
    "申請人分機": ["申請人分機", "申请人分机", "分機", "分机"],
    "放行單流出門崗": ["放行單流出門崗", "放行单流出门岗"],
    "放行單流入門崗": ["放行單流入門崗", "放行单流入门岗"],
    "實際放行門崗": ["實際放行門崗", "实际放行门岗"],
    "實際放行時間": ["實際放行時間", "实际放行时间"],
    "放行狀態": ["放行狀態", "放行状态"],
    "放行超時": ["放行超時", "放行超时"],
    "接收時間": ["接收時間", "接收时间"],
    "接收超時": ["接收超時", "接收超时"],
    "接收狀態": ["接收狀態", "接收状态"],
    "接收人部門": ["接收人部門", "接收人部门"],
}
ALIAS_LOOKUP = {a: std for std, lst in FIELD_ALIASES.items() for a in lst}


# ---------------------------------------------------------------- 内存观测
def peak_rss_mb():
    """取当前进程峰值工作集（Windows）。失败返回 None。"""
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

        k32 = ctypes.WinDLL("kernel32")
        psapi = ctypes.WinDLL("psapi")
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        if not psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return None
        return pmc.PeakWorkingSetSize / 1024 / 1024
    except Exception:
        return None


# ---------------------------------------------------------------- 读 xlsx（流式）
def col_index(ref):
    """'AB12' → 27（0 起）"""
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + (ord(ch.upper()) - 64)
        else:
            break
    return n - 1


def _cell_text(c, sst):
    t = c.get("t")
    if t == "inlineStr":
        node = c.find(NS + "is")
        if node is None:
            return ""
        return "".join(x.text or "" for x in node.iter(NS + "t"))
    v = c.find(NS + "v")
    if v is None or v.text is None:
        return ""
    if t == "s":
        try:
            return sst[int(v.text)]
        except Exception:
            return ""
    return v.text


def iter_xlsx(path):
    """流式逐行产出 list[str]。自动找第一个工作表、自动加载 sharedStrings。"""
    z = zipfile.ZipFile(path)
    names = z.namelist()
    sst = []
    if "xl/sharedStrings.xml" in names:
        with z.open("xl/sharedStrings.xml") as f:
            buf = []
            for ev, el in ET.iterparse(f, events=("end",)):
                if el.tag == NS + "si":
                    buf.append("".join(t.text or "" for t in el.iter(NS + "t")))
                    el.clear()
            sst = buf
    sheet = "xl/worksheets/sheet1.xml"
    if sheet not in names:
        cands = sorted(n for n in names if n.startswith("xl/worksheets/sheet"))
        if not cands:
            raise SystemExit("xlsx 里找不到工作表")
        sheet = cands[0]
    with z.open(sheet) as f:
        row = None
        for ev, el in ET.iterparse(f, events=("start", "end")):
            if ev == "start" and el.tag == NS + "row":
                row = {}
                continue
            if ev == "end" and el.tag == NS + "row":
                if row is not None:
                    width = (max(row) + 1) if row else 0
                    yield [row.get(i, "") for i in range(width)]
                el.clear()
                row = None
                continue
            if ev == "end" and el.tag == NS + "c" and row is not None:
                idx = col_index(el.get("r", ""))
                row[idx] = _cell_text(el, sst)
                el.clear()


def iter_csv(path):
    raw = open(path, "rb").read(65536)
    for enc in ("utf-8-sig", "gbk", "utf-8"):
        try:
            raw.decode(enc)
            break
        except Exception:
            continue
    else:
        enc = "utf-8"
    with open(path, "r", encoding=enc, newline="", errors="replace") as f:
        for row in csv.reader(f):
            yield row


def find_header(rows_iter, max_scan=25):
    """找到表头行：命中 ≥2 个已知别名。返回 (标准名列表, 剩余迭代入口)。"""
    buf = []
    for i, row in enumerate(rows_iter):
        buf.append(row)
        hits = sum(1 for v in row if ALIAS_LOOKUP.get(str(v).strip()))
        if hits >= 2:
            header = [ALIAS_LOOKUP.get(str(v).strip(), str(v).strip()) for v in row]
            return header, buf[i + 1:], rows_iter
        if i >= max_scan:
            break
    raise SystemExit("前 25 行里没找到可识别的表头（应有 放行單號 / 申請日期 等列）")


def convert_xlsx_to_csv(xlsx_path, csv_path):
    """一次性把 xlsx 转成 CSV（流式，内存不随行数长）。

    xlsx 的 XML 解析约 2.5k 行/秒，同数据的 CSV 解析约 3.5 万行/秒（实测）。
    口径要反复调时，先转一次 CSV，后续所有配方重跑都能快一个数量级。
    """
    t = time.time()
    n = 0
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)) or ".", exist_ok=True)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        for row in iter_xlsx(xlsx_path):
            w.writerow(row)
            n += 1
            if n % 100000 == 0:
                print(f"  ... 转换 {n:,} 行  {time.time() - t:.0f}s", flush=True)
    size_mb = os.path.getsize(csv_path) / 1024 / 1024
    print(f"已转 CSV：{csv_path}（{n:,} 行 / {size_mb:.1f} MB / {time.time() - t:.0f}s）", flush=True)
    return csv_path


# ---------------------------------------------------------------- 口径工具
def num(v):
    try:
        s = str(v).strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None


def to_time(v):
    s = str(v).strip()
    if not s:
        return None
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M",
                "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def dept_l1(name):
    """一级部门：去末尾「_厂区」再取第一个空白之前。MFG 網站 SW 自動化1組_鄭州 → MFG"""
    s = str(name or "").strip()
    if not s:
        return "（空）"
    s = re.sub(r"_[^_]*$", "", s) if "_" in s else s
    return s.split()[0] if s.split() else s


def duration_bucket(minutes, edges):
    """edges 例：[30, 60, 240]，返回标签"""
    labels = []
    lo = 0
    for e in edges:
        labels.append(f"{lo}~{e}min" if lo else f"≤{e}min")
        lo = e
    labels.append(f">{edges[-1]}min")
    for i, e in enumerate(edges):
        if minutes <= e:
            return labels[i]
    return labels[-1]


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser(description="按配方清洗放行导出数据（L1）")
    ap.add_argument("--input", required=True, help="导出的 .xlsx 或 .csv")
    ap.add_argument("--recipe", required=True, help="配方 JSON 路径")
    ap.add_argument("--out", default="out", help="输出根目录（默认 out）")
    ap.add_argument("--batch", default=None, help="批次名，如 2026W48（默认按日期自动）")
    ap.add_argument("--no-spool", action="store_true", help="不生成明细子集（省一次读写）")
    ap.add_argument("--to-csv", action="store_true",
                    help="只把 xlsx 转成同名 CSV 后退出（预处理一次，之后所有配方跑 CSV 快约一个数量级）")
    ap.add_argument("--cache-csv", action="store_true",
                    help="xlsx 先转 CSV 再跑（同级已有且不比源文件旧的 CSV 直接复用）")
    ap.add_argument("--min-minutes", type=float, default=None,
                    help="覆盖配方的 detail_subset.min_minutes：子集只留超时 ≥N 分钟的单")
    args = ap.parse_args()

    t0 = time.time()
    recipe = json.load(open(args.recipe, encoding="utf-8"))
    thr = recipe.get("thresholds", {})
    edges = recipe.get("duration_buckets_min", [30, 60, 240])
    top_n = int(recipe.get("top_n", 12))
    batch = args.batch or datetime.now().strftime("%Y%m%d")
    outdir = os.path.join(args.out, batch)
    os.makedirs(outdir, exist_ok=True)

    # ---- 输入准备：xlsx 慢在 XML 解析（实测 ~2.5k 行/秒），CSV 快约一个数量级 ----
    input_path = args.input
    is_xlsx = input_path.lower().endswith((".xlsx", ".xlsm"))
    if is_xlsx and args.to_csv:
        convert_xlsx_to_csv(input_path, os.path.splitext(input_path)[0] + ".csv")
        return
    if is_xlsx and args.cache_csv:
        cache = os.path.splitext(input_path)[0] + ".csv"
        fresh = os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(input_path)
        if not fresh:
            convert_xlsx_to_csv(input_path, cache)
        else:
            print(f"复用已转好的 CSV：{cache}", flush=True)
        input_path = cache

    src = iter_xlsx(input_path) if input_path.lower().endswith((".xlsx", ".xlsm")) else iter_csv(input_path)
    header, pending, rest = find_header(src)

    def all_rows():
        for r in pending:
            yield r
        for r in rest:
            yield r

    idx = {name: i for i, name in enumerate(header)}
    need = ["申請日期", "放行單號", "申請人部門", "物品類型", "物品分類", "放行超時",
            "接收超時", "接收時間", "放行單流入門崗", "實際放行門崗", "放行狀態", "接收狀態"]
    missing = [n for n in need if n not in idx]
    width = len(header)

    spool_path = os.path.join(outdir, "_spool.csv")
    spool = None if args.no_spool else open(spool_path, "w", encoding="utf-8-sig", newline="")
    spool_w = csv.writer(spool) if spool else None
    if spool_w:
        spool_w.writerow(header)

    orders = {}
    n_rows = 0
    last_tick = time.time()

    for row in all_rows():
        if not row or all(v == "" for v in row):
            continue
        row = list(row) + [""] * (width - len(row))
        n_rows += 1
        if spool_w:
            spool_w.writerow(row)
        if n_rows % 50000 == 0:
            el = time.time() - t0
            print(f"  ... {n_rows:,} 行  已用 {el:.0f}s  峰值内存 {peak_rss_mb() or 0:.0f}MB", flush=True)
            last_tick = time.time()

        def g(name):
            i = idx.get(name)
            return row[i] if i is not None and i < len(row) else ""

        bill = str(g("放行單號")).strip()
        if not bill:
            continue
        o = orders.get(bill)
        if o is None:
            o = orders[bill] = {
                "單號": bill,
                "日期": str(g("申請日期")).strip()[:10],
                "部門": str(g("申請人部門")).strip(),
                "物品類型": str(g("物品類型")).strip(),
                "物品分類": str(g("物品分類")).strip(),
                "流入門崗": str(g("放行單流入門崗")).strip(),
                "放行超時分鐘": 0.0,
                "接收超時分鐘": 0.0,
                "已到達": False,
                "有接收時間": False,
                "末筆狀態": "",
                "末筆接收狀態": "",
            }
        gate_in = str(g("放行單流入門崗")).strip()
        if str(g("實際放行門崗")).strip() and str(g("實際放行門崗")).strip() == gate_in:
            o["已到達"] = True
        rmin = num(g("放行超時")) or 0
        if rmin > o["放行超時分鐘"]:
            o["放行超時分鐘"] = rmin
        cmin = num(g("接收超時")) or 0
        if cmin > o["接收超時分鐘"]:
            o["接收超時分鐘"] = cmin
        if str(g("接收時間")).strip():
            o["有接收時間"] = True
        o["末筆狀態"] = str(g("放行狀態")).strip()
        if str(g("接收狀態")).strip():
            o["末筆接收狀態"] = str(g("接收狀態")).strip()

    if spool:
        spool.close()
    t_read = time.time() - t0
    print(f"读取完成：{n_rows:,} 行 / {len(orders):,} 单，用时 {t_read:.0f}s", flush=True)

    # ---------- 订单级派生 ----------
    for o in orders.values():
        rel = o["放行超時分鐘"]
        rec = o["接收超時分鐘"]
        o["在途"] = not o["已到達"]
        o["在途超時"] = o["在途"] and rel > 0
        o["到達超時"] = o["已到達"] and rel > 0
        o["超時未接收"] = o["已到達"] and rec > 0 and not o["有接收時間"]
        o["已接收但超時"] = o["已到達"] and rec > 0 and o["有接收時間"]
        o["放行超時"] = rel > 0
        o["接收超時"] = rec > 0
        o["超時"] = o["放行超時"] or o["接收超時"]
        o["超時分鐘"] = max(rel, rec)
        o["結案"] = o["已到達"] and not o["在途超時"]
        o["一級部門"] = dept_l1(o["部門"])
        o["時長檔"] = duration_bucket(rel, edges) if rel > 0 else "未超时"

    total = len(orders)
    kpi = {
        "批次": batch,
        "源文件": os.path.basename(args.input),
        "原始行数": n_rows,
        "放行单数": total,
        "已到达单数": sum(1 for o in orders.values() if o["已到達"]),
        "在途单数": sum(1 for o in orders.values() if o["在途"]),
        "结案率": round(sum(1 for o in orders.values() if o["結案"]) / total, 4) if total else 0,
        "放行超时单数": sum(1 for o in orders.values() if o["放行超時"]),
        "接收超时单数": sum(1 for o in orders.values() if o["接收超時"]),
        "超时未接收单数": sum(1 for o in orders.values() if o["超時未接收"]),
        "在途超时单数": sum(1 for o in orders.values() if o["在途超時"]),
        "到达超时单数": sum(1 for o in orders.values() if o["到達超時"]),
        "超时单数(广义)": sum(1 for o in orders.values() if o["超時"]),
        "超时率": round(sum(1 for o in orders.values() if o["超時"]) / total, 4) if total else 0,
        "放行超时总小时": round(sum(o["放行超時分鐘"] for o in orders.values()) / 60, 1),
    }

    # ---------- 各维度 ----------
    def agg(group):
        n = len(group)
        ov = [o for o in group if o["超時"]]
        rel = [o for o in group if o["放行超時"]]
        return {
            "单数": n,
            "超时单数": len(ov),
            "超时率": round(len(ov) / n, 4) if n else 0,
            "放行超时单数": len(rel),
            "平均放行超时分钟": round(sum(o["放行超時分鐘"] for o in rel) / len(rel), 1) if rel else 0,
            "最长放行超时分钟": int(max((o["放行超時分鐘"] for o in rel), default=0)),
            "超时未接收": sum(1 for o in group if o["超時未接收"]),
            "在途超时": sum(1 for o in group if o["在途超時"]),
        }

    dims = recipe.get("dimensions", [])
    written = []
    for k, dim in enumerate(dims, start=2):
        key = dim["key"]
        groups = {}
        for o in orders.values():
            v = o.get(key, "（空）") or "（空）"
            groups.setdefault(v, []).append(o)
        rows = []
        for v, gp in groups.items():
            a = agg(gp)
            a["维度值"] = v
            rows.append(a)
        rows.sort(key=lambda x: (-x["超时单数"], -x["单数"]))
        if dim.get("top"):
            rows = rows[: int(dim["top"])]
        cols = ["维度值", "单数", "超时单数", "超时率", "放行超时单数", "平均放行超时分钟",
                "最长放行超时分钟", "超时未接收", "在途超时"]
        fn = os.path.join(outdir, f"{k:02d}_按{dim.get('label', key)}.csv")
        with open(fn, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in cols})
        written.append((os.path.basename(fn), len(rows)))

    # ---------- 时长分档 ----------
    bucket_labels = []
    lo = 0
    for e in edges:
        bucket_labels.append(f"≤{e}min" if lo == 0 else f"{lo}~{e}min")
        lo = e
    bucket_labels.append(f">{edges[-1]}min")
    buckets = {b: [] for b in bucket_labels}
    for o in orders.values():
        if o["放行超時"]:
            buckets[o["時長檔"]].append(o)
    fn = os.path.join(outdir, "09_时长分档.csv")
    with open(fn, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["时长档", "单数", "占超时单比", "单号样例(前3)"])
        rel_total = sum(len(v) for v in buckets.values()) or 1
        for b in bucket_labels:
            gp = buckets[b]
            gp.sort(key=lambda o: -o["放行超時分鐘"])
            w.writerow([b, len(gp), f"{len(gp) / rel_total:.1%}",
                        " / ".join(o["單號"] for o in gp[:3])])
    written.append(("09_时长分档.csv", len(bucket_labels)))

    # ---------- 明细子集 ----------
    if spool_w and os.path.exists(spool_path):
        rule = (recipe.get("detail_subset") or {}).get("rule", "release_or_unreceived")
        min_min = args.min_minutes if args.min_minutes is not None \
            else float((recipe.get("detail_subset") or {}).get("min_minutes", 0) or 0)

        def keep(o):
            if o["超時分鐘"] < min_min:
                return False
            if rule == "all_overtime":
                return o["超時"]
            if rule == "overtime_or_transit":
                return o["超時"] or o["在途"]
            return o["放行超時"] or o["超時未接收"]

        interesting = {b for b, o in orders.items() if keep(o)}
        fn = os.path.join(outdir, "09_明细_超时单.csv")
        tmp_fn = fn + ".tmp"
        kept = 0
        with open(spool_path, "r", encoding="utf-8-sig", newline="") as fin, \
                open(tmp_fn, "w", encoding="utf-8-sig", newline="") as fout:
            rd, wr = csv.reader(fin), csv.writer(fout)
            head = next(rd)
            wr.writerow(head)
            bi = head.index("放行單號") if "放行單號" in head else 1
            for r in rd:
                if len(r) > bi and r[bi] in interesting:
                    wr.writerow(r)
                    kept += 1
        # 先写 .tmp 再替换：输出目录可能被 OneDrive 同步/杀软占用，直接开 "w" 偶发 OSError 22
        for attempt in range(5):
            try:
                os.replace(tmp_fn, fn)
                break
            except OSError:
                if attempt == 4:
                    raise
                time.sleep(1.5)
        os.remove(spool_path)
        written.append(("09_明细_超时单.csv", kept))
        size_mb = os.path.getsize(fn) / 1024 / 1024
        print(f"\n明细子集：{kept:,} 行 / {size_mb:.1f} MB / {len(interesting):,} 单（规则 {rule}"
              + (f"，超时≥{min_min:g}分钟" if min_min else "") + "）")
        if size_mb > 80:
            print("  ⚠️ 子集偏大，4GB 机器拖进看板会吃力。可把配方 detail_subset.min_minutes 提到 60 或 120，或改 rule=all_overtime 再筛。")

    with open(os.path.join(outdir, "01_KPI.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(kpi.keys()))
        w.writeheader()
        w.writerow(kpi)
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(kpi, f, ensure_ascii=False, indent=2)

    el = time.time() - t0
    print("\n=== 周报口径摘要 ===")
    for k in ("放行单数", "结案率", "放行超时单数", "接收超时单数", "超时未接收单数",
              "在途超时单数", "超时率", "放行超时总小时"):
        print(f"  {k}: {kpi[k]}")
    print("\n=== 产物 ===")
    print(f"  01_KPI.csv / summary.json")
    for name, cnt in written:
        print(f"  {name}  ({cnt} 行)")
    print(f"\n输出目录: {outdir}")
    print(f"总耗时: {el:.0f}s（读取 {t_read:.0f}s）  峰值内存: {peak_rss_mb() or 0:.0f} MB")
    if is_xlsx and not args.cache_csv:
        print(f"提示：本次直接解析 xlsx（读取 {t_read:.0f}s）。口径要反复调时加 --cache-csv："
              f"转一次 CSV 后重跑，读取约降到 {max(t_read / 9, 1):.0f}s 量级。")
    if missing:
        print(f"⚠️ 源文件缺少列（相关指标会失真）: {missing}")


if __name__ == "__main__":
    main()
