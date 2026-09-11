# -*- coding: utf-8 -*-
"""门岗压力演示数据：固定门岗池 + 流量向 2～3 个岗倾斜，供卡 A / 卡 B 验收。

口径与 gen_monitor_data_v3.py 相同（WF9897、整单分类、超时打末笔）。
输出：物品放行监控_门岗压力演示.xlsx（xlsx 被 gitignore，需本地生成）。
"""
import random, datetime, openpyxl
from pathlib import Path

random.seed(2026091201)
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "物品放行监控_原备份.xlsx"
OUT = ROOT / "物品放行监控_门岗压力演示.xlsx"
if not SRC.exists():
    raise SystemExit(f"找不到表头模板：{SRC}")

headers = [c.value for c in openpyxl.load_workbook(SRC).active[1]]
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "物品放行监控"
ws.append(headers)

# 16 个固定岗。前两个 = 滞留高压；前三个 = 过货高压（中码头/物流门又堵又忙，南一门只忙不堵）
GATES = [
    "ZZ-L07-1F-中碼頭崗",
    "ZZ-D07-1F-物流門",
    "ZZ-A01-1F-南一門",
    "ZZ-A01-1F-南二門",
    "ZZ-B02-1F-北一門",
    "ZZ-B02-1F-北二門",
    "ZZ-C03-2F-東門",
    "ZZ-C03-2F-西門",
    "ZZ-D04-1F-員工通道",
    "ZZ-D04-1F-訪客門",
    "ZZ-L05-3F-南一門",
    "ZZ-A06-2F-中碼頭崗",
    "ZZ-B07-1F-物流門",
    "ZZ-C08-4F-東門",
    "ZZ-D09-2F-西門",
    "ZZ-L08-1F-南二門",
]
HOT_STUCK = GATES[:2]
HOT_LOAD = GATES[:3]

names = ["劉斌","周勇","趙飛","張巧莉","郝強","馬萬玉","王偉","李娜","陳靜","楊帆",
         "黃磊","吳婷","鄭浩","孫琳","朱軍","胡敏","郭強","林芳","何勇","高翔"]
depts = ["MLB 撕石墨片 A線_ZZ","MFG 網站 SW 自動化1組_鄭州","物流 倉儲課_鄭州",
         "MLB 組裝 測試線_ZZ","設備 工程課_鄭州","新產品 試製線_鄭州"]
models = ["DeLorean","ModelX","Aurora","Phoenix"]
item_names = ["MLB","網卡","螺絲","主機板","測試機台","光纖模組","電池","治具"]
units = ["PCS","BOX","SET"]
item_class_common = ["生產物料(非A類)","耗材","资讯物品","设备"]

def gen_emp(prefix):
    return prefix + str(random.randint(1000000, 9999999))

def fmt(dt):
    return dt.strftime("%Y/%m/%d %H:%M:%S")

seq = 0
def gen_bill_no(special, apply_dt):
    global seq
    seq += 1
    code = "9897" if special else "7501"
    return f"WF{code}{apply_dt.strftime('%y%m%d')}{seq:06d}"

def make_emp_pair(prefix=None):
    p = prefix or random.choice(["H", "F"])
    return gen_emp(p), random.choice(names)

def pick_in_gate(in_transit):
    r = random.random()
    if in_transit:
        if r < 0.46:
            return HOT_STUCK[0]
        if r < 0.74:
            return HOT_STUCK[1]
        return random.choice(GATES[2:])
    if r < 0.10:
        return HOT_STUCK[0]
    if r < 0.20:
        return HOT_STUCK[1]
    return random.choice(GATES[2:])

def pick_out_gate(avoid):
    g = random.choice(GATES)
    while g == avoid:
        g = random.choice(GATES)
    return g

def pick_hop(path, in_gate, arrived):
    banned = set(path)
    if not arrived:
        banned.add(in_gate)
    r = random.random()
    if r < 0.42:
        cand = HOT_LOAD[0]
    elif r < 0.66:
        cand = HOT_LOAD[1]
    elif r < 0.82:
        cand = HOT_LOAD[2]
    else:
        cand = random.choice(GATES[3:])
    if cand not in banned:
        return cand
    pool = [g for g in GATES if g not in banned]
    return random.choice(pool) if pool else None

def pick_status():
    r = random.random()
    if r < 0.50:
        return "arrived_ontime"
    if r < 0.62:
        return "arrived_late_release"
    if r < 0.70:
        return "arrived_recv_timeout"
    if r < 0.78:
        return "arrived_no_recv"
    return "in_transit"

TARGET_ROWS = 3000
start = datetime.datetime(2026, 8, 3, 7, 0, 0)
end = datetime.datetime(2026, 8, 8, 22, 0, 0)
stat_count = {}
bill_count = 0

while ws.max_row - 1 < TARGET_ROWS:
    special = random.random() < 0.18
    if special:
        item_type = random.choice(["新产品A级物料", "新产品机台"])
        item_class = item_type
    else:
        item_type = "普通物品"
        item_class = random.choice(item_class_common)

    apply_dt = start + datetime.timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
    bill_no = gen_bill_no(special, apply_dt)
    status = pick_status()
    stat_count[status] = stat_count.get(status, 0) + 1
    bill_count += 1

    arrived = status != "in_transit"
    in_gate = pick_in_gate(not arrived)
    out_gate = pick_out_gate(in_gate)

    app_id, app_name = make_emp_pair("H")
    app_dept = random.choice(depts)
    app_ext = str(random.randint(30000, 69999))
    if random.random() < 0.8:
        carry_id, carry_name, carry_dept, carry_ext = app_id, app_name, app_dept, app_ext
    else:
        carry_id, carry_name = make_emp_pair("H")
        carry_dept = random.choice(depts)
        carry_ext = str(random.randint(30000, 69999))

    model = random.choice(models) if (special or random.random() < 0.5) else ""
    item_name = random.choice(item_names)
    unit = random.choice(units)
    qty = random.randint(1, 500)
    item_id = str(random.randint(10000000, 39999999))
    remark = random.choice(["急件", "試製", "", ""])
    manager_id, _ = make_emp_pair("F")
    source = random.choice(["手動提單", "系統自動", "ERP同步"])
    customs = gen_emp("") if (special and random.random() < 0.5) else ""
    if random.random() < 0.3:
        conf_id, conf_name = make_emp_pair("H")
    else:
        conf_id, conf_name = "", ""

    path = [out_gate]
    extra = random.randint(1, 2) if not arrived else random.randint(0, 2)
    for _ in range(extra):
        hop = pick_hop(path, in_gate, arrived)
        if hop:
            path.append(hop)
    if arrived:
        path.append(in_gate)

    release_times = []
    t = apply_dt + datetime.timedelta(minutes=random.randint(10, 180))
    for _ in path:
        release_times.append(t)
        t = t + datetime.timedelta(minutes=random.randint(30, 200))

    deadline_arrival = apply_dt + datetime.timedelta(hours=12)
    if arrived:
        if status == "arrived_late_release":
            release_times[-1] = deadline_arrival + datetime.timedelta(hours=random.randint(1, 8))
        elif release_times[-1] > deadline_arrival:
            release_times[-1] = deadline_arrival - datetime.timedelta(minutes=random.randint(10, 120))
    arrival_time = release_times[-1] if arrived else None
    in_transit_timeout = (not arrived) and random.random() < 0.55

    recv_id = recv_name = recv_dept = recv_time = recv_status = ""
    recv_timeout = "0"
    if status == "arrived_recv_timeout":
        recv_id, recv_name = make_emp_pair("H")
        recv_dept = random.choice(depts)
        recv_time = arrival_time + datetime.timedelta(hours=random.randint(3, 10))
        recv_status = "正常"
        recv_timeout = "1"
    elif status == "arrived_ontime":
        recv_id, recv_name = make_emp_pair("H")
        recv_dept = random.choice(depts)
        recv_time = arrival_time + datetime.timedelta(minutes=random.randint(10, 90))
        recv_status = "正常"
    elif status == "arrived_no_recv":
        recv_status = "未接收"
        recv_timeout = "1"
    elif status == "arrived_late_release":
        if random.random() < 0.5:
            recv_id, recv_name = make_emp_pair("H")
            recv_dept = random.choice(depts)
            recv_time = arrival_time + datetime.timedelta(minutes=random.randint(10, 90))
            recv_status = "正常"
        else:
            recv_status = "未接收"

    for idx, gate in enumerate(path):
        is_last = (idx == len(path) - 1)
        rel_id, rel_name = make_emp_pair("F")
        rel_status = "正常" if random.random() < 0.95 else "異常"
        if is_last:
            if status == "arrived_late_release":
                rel_timeout = "1"
            elif not arrived:
                rel_timeout = "1" if in_transit_timeout else "0"
            else:
                rel_timeout = "0"
        else:
            rel_timeout = "0"
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
        ws.append([row.get(h, "") for h in headers])

wb.save(OUT)
print("完成. 输出:", OUT)
print("总行数:", ws.max_row - 1, " 单号数:", bill_count)
print("状态分布:", stat_count)
print("固定门岗数:", len(GATES), "滞留倾斜:", HOT_STUCK, "过货倾斜:", HOT_LOAD)
