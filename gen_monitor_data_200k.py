# -*- coding: utf-8 -*-
"""物品放行监控_生成_200k.xlsx —— 大数据量压测数据生成器（以 gen_monitor_data_v3.py 为底）

用途：模拟「系统一周量级」的导出文件，验看板在大文件下的解析性能与交互。
默认 200,000 单（约 58 万行、130MB 左右）；日常小样本请用 gen_monitor_data_v3.py。

与 V3 的关系
------------
* 业务规则、字段格式、状态分布与 V3 完全一致（同一套池子与判定逻辑），
  所以两个脚本产出的数据在看板上口径相同，可直接对比。
* 差别只有三点：
  1. 规模：默认 20 万单（V3 是 1200 行小样本）；
  2. 日期窗口：默认「运行当天往前 7 个完整自然日」（V3 固定 8 月某 5 天）；
  3. 导出样式：默认第 1 行合并空白、第 2 行表头（与系统真实导出、旧 100k 一致）。

实现要点
--------
* 用 openpyxl 的 write_only 模式流式写盘：58 万行 × 40 列若用普通模式会占数 GB 内存。
* write_only 不支持 merge_cells，故保存后对 xlsx 内的 sheet XML 注入 <mergeCells>（见 inject_merged_header）。

导出字段格式（2026-11-12 起，与系统原始导出一致）
------------------------------------------------
  放行狀態：正常 / 超时 / 放行拒绝（超时行固定「超时」）
  放行超時：0 或 超时分钟数（>0 整数；与放行狀態「超时」一一对应）
  接收超時：0 或 超时分钟数（>0 整数）
  接收狀態：未接收 / 未接收超时 / 正常 / 超时
  物品類型：特级安保物品 / 普通物品（物品分類 6 类细分保持不变）

用法
----
  py gen_monitor_data_200k.py                        # 默认 20 万单，写根目录 物品放行监控_生成_200k.xlsx
  py gen_monitor_data_200k.py --bills 150000         # 15 万单
  py gen_monitor_data_200k.py --end-date 2026-11-26  # 指定窗口截止日（往前 7 天）
  py gen_monitor_data_200k.py --no-merged-header     # 表头放第 1 行（不补合并空白行，省一次 zip 重写）
"""
import argparse
import codecs
import csv
import datetime
import hashlib
import random
import shutil
import time
import zipfile
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "物品放行监控_原备份.xlsx"          # 只用来取 40 列表头模板
DEFAULT_OUT = ROOT / "物品放行监控_生成_200k.xlsx"

RELEASE_LIMIT_H = 12   # 申请后 12 小时内应到达流入门岗
RECV_LIMIT_H = 2       # 到达后 2 小时内应完成接收

# ---------- 基础数据池（与 gen_monitor_data_v3.py 完全一致） ----------
NAMES = ["劉斌", "周勇", "趙飛", "張巧莉", "郝強", "馬萬玉", "王偉", "李娜", "陳靜", "楊帆",
         "黃磊", "吳婷", "鄭浩", "孫琳", "朱軍", "胡敏", "郭強", "林芳", "何勇", "高翔",
         "劉洋", "徐麗", "羅傑", "梁爽", "宋佳", "唐磊", "韓雪", "馮濤", "董潔", "曹宇"]
DEPTS = ["MLB 撕石墨片 A線_ZZ", "MFG 網站 SW 自動化1組_鄭州", "MFG 網站 SW 自動化2組_鄭州",
         "MLB 主板 SMT 一課_ZZ", "MLB 組裝 測試線_ZZ", "資訊 系統維運課_鄭州",
         "設備 工程課_鄭州", "物流 倉儲課_鄭州", "品保 IQC 課_鄭州", "新產品 試製線_鄭州"]
ZONES = ["D", "L", "C", "B", "A"]
BUILDINGS = ["01", "02", "03", "04", "05", "06", "07", "08", "09"]
FLOORS = ["1F", "2F", "3F", "4F"]
GATE_NAMES = ["南一門", "南二門", "北一門", "北二門", "中碼頭崗", "東門", "西門", "員工通道", "物流門", "訪客門"]
MODELS = ["DeLorean", "ModelX", "Aurora", "Phoenix", "Titan", "Nova", "Orion", "Vega"]
ITEM_NAMES = ["MLB", "網卡", "螺絲", "鋼板", "標簽紙", "防靜電袋", "主機板", "測試機台", "光纖模組",
              "電池", "連接器", "散熱片", "治具", "攝像頭模組", "載板", "排線", "馬達", "閥件", "感測器", "外殼"]
UNITS = ["PCS", "BOX", "KG", "SET", "LOT", "ROLL"]
ITEM_CLASS_COMMON = ["生產物料(非A類)", "耗材", "资讯物品", "设备"]

# 门岗组合池：5 × 9 × 4 × 10 = 1800 种，与真实导出的门岗数量级一致
GATES = [f"ZZ-{z}{b}-{f}-{g}" for z in ZONES for b in BUILDINGS for f in FLOORS for g in GATE_NAMES]


def gen_emp(prefix):
    return prefix + str(random.randint(1000000, 9999999))


def fmt(dt):
    return dt.strftime("%Y/%m/%d %H:%M:%S")


def make_emp_pair(prefix=None):
    p = prefix or random.choice(["H", "F"])
    return gen_emp(p), random.choice(NAMES)


def overtime_minutes(actual_dt, deadline_dt, seed):
    """超时分钟数：优先用真实时限差推导；推导不出时用单号稳定的 30~600 分钟。未超时返回 "0"。"""
    if actual_dt and deadline_dt:
        m = int((actual_dt - deadline_dt).total_seconds() // 60)
        if m > 0:
            return str(min(m, 10080))
    h = int(hashlib.md5(seed.encode("utf-8")).hexdigest()[:8], 16)
    return str(30 + h % 571)


def pick_status():
    r = random.random()
    if r < 0.55: return "arrived_ontime"          # 正常结案
    if r < 0.67: return "arrived_late_release"    # 到达超时
    if r < 0.75: return "arrived_recv_timeout"    # 已接收但接收时超时
    if r < 0.83: return "arrived_no_recv"         # 超时未接收
    return "in_transit"                           # 在途（约 45% 为在途超时）


SHEET_XML = "xl/worksheets/sheet1.xml"


def inject_merged_header(path, ncol):
    """给已保存的 xlsx 注入「第 1 行 A1:AN1 合并」，等效 openpyxl 的 merge_cells。

    write_only 模式不支持 merge_cells，故保存后改 sheet XML。**必须插在 `</sheetData>`
    之后**——OOXML 的子节点顺序是 sheetData → mergeCells → pageMargins，
    放到 `</worksheet>` 前会使 mergeCells 落在 pageMargins 之后，Excel 会提示内容有问题。
    大文件（sheet XML 可到 1.4GB）用增量解码流式改写，避免整块读进内存。
    可重复执行：已有的合并块会先被移除再按正确位置插入。
    """
    ref = f"A1:{get_column_letter(ncol)}1"
    block = f'<mergeCells count="1"><mergeCell ref="{ref}"/></mergeCells>'
    anchor = "</sheetData>"
    tmp = path.with_name(path.stem + ".tmp" + path.suffix)
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename != SHEET_XML:
                zout.writestr(item, zin.read(item.filename))
                continue
            dec = codecs.getincrementaldecoder("utf-8")()
            inserted = False
            with zin.open(item.filename) as fin, zout.open(item, "w") as fout:
                carry = ""
                keep = max(len(block), len(anchor)) + 16
                while True:
                    chunk = fin.read(1 << 20)
                    if not chunk:
                        break
                    buf = carry + dec.decode(chunk)
                    buf = buf.replace(block, "")            # 去掉旧位置上的合并块
                    if not inserted and anchor in buf:
                        buf = buf.replace(anchor, anchor + block, 1)
                        inserted = True
                    carry = buf[-keep:]
                    fout.write(buf[:-keep].encode("utf-8"))
                carry = carry.replace(block, "")
                if not inserted:
                    carry = carry.replace("</worksheet>", anchor + block + "</worksheet>")
                fout.write((carry + dec.decode(b"", final=True)).encode("utf-8"))
    shutil.move(str(tmp), str(path))


def main():
    ap = argparse.ArgumentParser(description="大数据量压测数据生成器（默认 20 万单）")
    ap.add_argument("--bills", type=int, default=200000, help="放行单数（默认 200000）")
    ap.add_argument("--seed", type=int, default=20261127, help="随机种子（默认 20261127）")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="输出路径")
    ap.add_argument("--end-date", default=None, help="窗口截止日 YYYY-MM-DD，往前取 7 个整日（默认今天）")
    ap.add_argument("--days", type=int, default=7, help="窗口天数（默认 7）")
    ap.add_argument("--no-merged-header", action="store_true",
                    help="表头放第 1 行，不补合并空白行（省一次 zip 重写）")
    ap.add_argument("--format", dest="fmt", choices=["xlsx", "csv"], default="xlsx",
                    help="输出格式：xlsx（默认，真实导出形态）/ csv（供看板大文件压测用，绕开 SheetJS 的 XML 体积上限）")
    args = ap.parse_args()

    if not SRC.exists():
        raise SystemExit(f"找不到表头模板：{SRC}（需要它取 40 列表头）")
    if args.bills <= 0:
        raise SystemExit("--bills 必须为正整数")

    random.seed(args.seed)

    out = Path(args.out)
    if args.fmt == "csv" and out.suffix.lower() != ".csv":
        out = out.with_suffix(".csv")

    # 体量预警：SheetJS（看板 lib/xlsx.full.min.js）在浏览器里解压后的 sheet XML 超过
    # 约 512MB（V8 单字符串上限）时会解析成空表，报「文件中没有可读取的工作表数据」。
    # 实测：100k 行 / 251MB 正常；291k 行 / 682MB、583k 行 / 1374MB 均失败。
    if args.fmt == "xlsx":
        est_rows = args.bills * 2.9
        est_xml_mb = est_rows * 2.4 / 1024
        if est_xml_mb > 480:
            print(f"⚠️  预计 {est_rows:,.0f} 行，解压后 sheet XML ≈ {est_xml_mb:,.0f} MB，"
                  f"超过浏览器解析上限（≈512MB）。看板加载可能报「文件中没有可读取的工作表数据」。",
                  flush=True)
            print("    压测建议改用 --format csv（CSV 走 Papa.parse，不受此限）；"
                  "要真实 xlsx 形态就把 --bills 降到 60000 以下。", flush=True)
    end_date = (datetime.date.fromisoformat(args.end_date) if args.end_date else datetime.date.today())
    end = datetime.datetime.combine(end_date, datetime.time(0, 0, 0))
    start = end - datetime.timedelta(days=args.days)
    span = int((end - start).total_seconds())

    headers = [c.value for c in openpyxl.load_workbook(SRC, read_only=True).active[1]]

    wb = ws = csv_f = writer = None
    if args.fmt == "csv":
        # CSV：UTF-8 BOM，Excel 双击不乱码；看板走 Papa.parse，不受 sheet XML 体积上限影响
        out.parent.mkdir(parents=True, exist_ok=True)
        csv_f = open(out, "w", newline="", encoding="utf-8-sig")
        writer = csv.writer(csv_f)
        writer.writerow(headers)
    else:
        wb = openpyxl.Workbook(write_only=True)
        ws = wb.create_sheet("物品放行监控")
        if not args.no_merged_header:
            ws.append([""] * len(headers))       # 第 1 行：合并空白（与系统导出一致）
        ws.append(headers)                        # 第 2 行（或第 1 行）：表头

    seq = 0
    stat_count = {}
    gates_used = set()
    t0 = time.time()
    rows_written = 0

    for n in range(args.bills):
        # —— 整单固定属性 ——
        special = random.random() < 0.18
        if special:
            item_class = random.choice(["新产品A级物料", "新产品机台"])
            item_type = "特级安保物品"
        else:
            item_type = "普通物品"
            item_class = random.choice(ITEM_CLASS_COMMON)

        apply_dt = start + datetime.timedelta(seconds=random.randint(0, span - 1))
        seq += 1
        bill_no = f"WF{'9897' if special else '7501'}{apply_dt.strftime('%y%m%d')}{seq:06d}"

        out_gate = random.choice(GATES)
        in_gate = random.choice(GATES)
        while in_gate == out_gate:
            in_gate = random.choice(GATES)
        gates_used.add(out_gate); gates_used.add(in_gate)

        status = pick_status()
        stat_count[status] = stat_count.get(status, 0) + 1

        app_id, app_name = make_emp_pair("H")
        app_dept = random.choice(DEPTS)
        app_ext = str(random.randint(30000, 69999))
        if random.random() < 0.8:
            carry_id, carry_name, carry_dept, carry_ext = app_id, app_name, app_dept, app_ext
        else:
            carry_id, carry_name = make_emp_pair("H")
            carry_dept = random.choice(DEPTS)
            carry_ext = str(random.randint(30000, 69999))

        model = random.choice(MODELS) if (special or random.random() < 0.5) else ""
        item_name = random.choice(ITEM_NAMES)
        unit = random.choice(UNITS)
        qty = random.randint(1, 500)
        item_id = str(random.randint(10000000, 39999999))
        remark = random.choice(["急件", "試製", "客退", "返修", "", ""]) if random.random() < 0.5 else ""
        manager_id, manager_name = make_emp_pair("F")
        source = random.choice(["手動提單", "系統自動", "ERP同步"])
        customs = gen_emp("") if (special and random.random() < 0.5) else ""
        if random.random() < 0.3:
            conf_id, conf_name = make_emp_pair("H")
        else:
            conf_id, conf_name = "", ""

        # —— 门岗路径 ——
        arrived = status != "in_transit"
        path = [out_gate]
        k = random.randint(1, 2) if not arrived else random.randint(0, 2)
        while len(path) < k + 1:
            g = random.choice(GATES)
            if g not in path and g != in_gate:
                path.append(g)
                gates_used.add(g)
        if arrived:
            path.append(in_gate)

        release_times = []
        t = apply_dt + datetime.timedelta(minutes=random.randint(10, 180))
        for _ in range(len(path)):
            release_times.append(t)
            t = t + datetime.timedelta(minutes=random.randint(30, 200))

        deadline_arrival = apply_dt + datetime.timedelta(hours=RELEASE_LIMIT_H)
        if arrived:
            if status == "arrived_late_release":
                release_times[-1] = deadline_arrival + datetime.timedelta(hours=random.randint(1, 8))
            elif release_times[-1] > deadline_arrival:
                release_times[-1] = deadline_arrival - datetime.timedelta(minutes=random.randint(10, 120))
        arrival_time = release_times[-1] if arrived else None
        in_transit_timeout = (not arrived) and random.random() < 0.45

        # —— 接收字段（仅末笔） ——
        recv_id = recv_name = recv_dept = recv_time = ""
        recv_timeout = "0"
        recv_deadline = (arrival_time + datetime.timedelta(hours=RECV_LIMIT_H)) if arrival_time else None
        if status == "arrived_recv_timeout":
            recv_id, recv_name = make_emp_pair("H")
            recv_dept = random.choice(DEPTS)
            recv_time = arrival_time + datetime.timedelta(hours=random.randint(3, 10))
            recv_status = "超时"
            recv_timeout = overtime_minutes(recv_time, recv_deadline, bill_no + "C")
        elif status == "arrived_ontime":
            recv_id, recv_name = make_emp_pair("H")
            recv_dept = random.choice(DEPTS)
            recv_time = arrival_time + datetime.timedelta(minutes=random.randint(10, 90))
            recv_status = "正常"
        elif status == "arrived_no_recv":
            recv_status = "未接收超时"
            recv_timeout = overtime_minutes(None, None, bill_no + "C")
        elif status == "arrived_late_release":
            if random.random() < 0.5:
                recv_id, recv_name = make_emp_pair("H")
                recv_dept = random.choice(DEPTS)
                recv_time = arrival_time + datetime.timedelta(minutes=random.randint(10, 90))
                recv_status = "正常"
            else:
                recv_status = "未接收"
        else:
            recv_status = "未接收"

        if status == "arrived_late_release":
            last_rel_timeout = overtime_minutes(release_times[-1], deadline_arrival, bill_no + "R")
        elif not arrived and in_transit_timeout:
            last_rel_timeout = overtime_minutes(None, None, bill_no + "R")
        else:
            last_rel_timeout = "0"

        for idx, gate in enumerate(path):
            is_last = (idx == len(path) - 1)
            rel_id, rel_name = make_emp_pair("F")
            rel_timeout = last_rel_timeout if is_last else "0"
            if rel_timeout != "0":
                rel_status = "超时"
            else:
                rel_status = "正常" if random.random() < 0.95 else "放行拒绝"

            row = {
                "申請日期": fmt(apply_dt),
                "放行單號": bill_no,
                "物品類型": item_type,
                "申請人工號": app_id,
                "申請人姓名": app_name,
                "申請人部門": app_dept,
                "申請人分機": app_ext,
                "實際攜帶人工號": carry_id,
                "實際攜帶人姓名": carry_name,
                "實際攜帶人部門": carry_dept,
                "實際攜帶人分機": carry_ext,
                "放行單流出門崗": out_gate,
                "放行單流入門崗": in_gate,
                "實際放行門崗": gate,
                "放行人工號": rel_id,
                "放行人姓名": rel_name,
                "實際放行時間": fmt(release_times[idx]),
                "放行狀態": rel_status,
                "放行超時": rel_timeout,
                "接收時間": fmt(recv_time) if (recv_time and is_last) else "",
                "接收超時": recv_timeout if is_last else "0",
                "接收狀態": recv_status if is_last else "",
                "接收人工號": recv_id if is_last else "",
                "接收人姓名": recv_name if is_last else "",
                "接收人部門": recv_dept if is_last else "",
                "物品分類": item_class,
                "機種": model,
                "放行物品名稱": item_name,
                "放行物品分類": item_class,
                "物品型號": gen_emp("") if random.random() < 0.4 else "",
                "放行單位": unit,
                "放行數量": qty,
                "物品ID": item_id,
                "物品信息備註": remark,
                "廠區": "鄭州",
                "簽核權限主管": manager_id,
                "資料來源": source,
                "報關單號": customs,
                "確認人工號": conf_id,
                "確認人姓名": conf_name,
            }
            vals = [row.get(h, "") for h in headers]
            if ws is not None:
                ws.append(vals)
            else:
                writer.writerow(vals)
            rows_written += 1

        if (n + 1) % 20000 == 0:
            el = time.time() - t0
            print(f"  ... {n + 1:,} 单 / {rows_written:,} 行  已用 {el:.0f}s", flush=True)

    print(f"写盘完成：{rows_written:,} 行，用时 {time.time() - t0:.0f}s，开始保存…", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.fmt == "csv":
        csv_f.close()
        t_save = time.time() - t0
        header_note = "第 1"
    else:
        wb.save(out)
        t_save = time.time() - t0
        if not args.no_merged_header:
            print("补合并空白首行…", flush=True)
            inject_merged_header(out, len(headers))
        header_note = "第 2" if not args.no_merged_header else "第 1"

    size_mb = out.stat().st_size / 1024 / 1024
    print("完成. 输出:", out)
    print(f"总行数: {rows_written:,}（表头 {header_note} 行）"
          f"  单号数: {args.bills:,}  平均 {rows_written / max(args.bills, 1):.2f} 行/单")
    print(f"不同放行门岗: {len(gates_used)} / {len(GATES)}    窗口: {start:%Y-%m-%d} ~ {end:%Y-%m-%d}（前 {args.days} 天）")
    print(f"状态分布: {stat_count}")
    print(f"文件大小: {size_mb:.1f} MB    总耗时: {time.time() - t0:.0f}s（保存前 {t_save:.0f}s）")


if __name__ == "__main__":
    main()
