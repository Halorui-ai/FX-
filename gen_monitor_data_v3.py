# -*- coding: utf-8 -*-
# 物品放行监控_模拟测试.xlsx 生成脚本（v3，符合真实放行系统业务规则）
# 业务规则：
#   1. 一张放行单建单后物品种类固定 —— 物品分类整单唯一，多记录仅因经过不同门岗产生；
#   2. 超时/接收状态记录在最后一笔记录上（最后一笔决定整单状态）；
#   3. 特保单号前缀 WF9897（v2.2.0 起唯一判定依据；旧 WF8888 规则已废弃）；
#   4. 特保单物品分类仅「新产品A级物料」「新产品机台」两种；
#   5. 状态覆盖：正常结案 / 到达超时 / 已接收但接收时超时 / 超时未接收 / 在途超时 / 在途正常。
import random, datetime, openpyxl
from pathlib import Path

random.seed(2026080901)
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "物品放行监控_原备份.xlsx"
OUT = ROOT / "物品放行监控_模拟测试.xlsx"
if not SRC.exists():
    raise SystemExit(f"找不到表头模板：{SRC}")

src = openpyxl.load_workbook(SRC)
headers = [c.value for c in src.active[1]]

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "物品放行监控"
ws.append(headers)

# ---------- 基础数据池 ----------
names = ["劉斌","周勇","趙飛","張巧莉","郝強","馬萬玉","王偉","李娜","陳靜","楊帆",
         "黃磊","吳婷","鄭浩","孫琳","朱軍","胡敏","郭強","林芳","何勇","高翔",
         "劉洋","徐麗","羅傑","梁爽","宋佳","唐磊","韓雪","馮濤","董潔","曹宇"]
depts = ["MLB 撕石墨片 A線_ZZ","MFG 網站 SW 自動化1組_鄭州","MFG 網站 SW 自動化2組_鄭州",
         "MLB 主板 SMT 一課_ZZ","MLB 組裝 測試線_ZZ","資訊 系統維運課_鄭州",
         "設備 工程課_鄭州","物流 倉儲課_鄭州","品保 IQC 課_鄭州","新產品 試製線_鄭州"]
zones = ["D","L","C","B","A"]
buildings = ["01","02","03","04","05","06","07","08","09"]
floors = ["1F","2F","3F","4F"]
gate_names = ["南一門","南二門","北一門","北二門","中碼頭崗","東門","西門","員工通道","物流門","訪客門"]
models = ["DeLorean","ModelX","Aurora","Phoenix","Titan","Nova","Orion","Vega"]
item_names = ["MLB","網卡","螺絲","鋼板","標簽紙","防靜電袋","主機板","測試機台","光纖模組",
              "電池","連接器","散熱片","治具","攝像頭模組","載板","排線","馬達","閥件","感測器","外殼"]
units = ["PCS","BOX","KG","SET","LOT","ROLL"]
item_class_common = ["生產物料(非A類)","耗材","资讯物品","设备"]

def gen_gate():
    return f"ZZ-{random.choice(zones)}{random.choice(buildings)}-{random.choice(floors)}-{random.choice(gate_names)}"

def gen_emp(prefix):
    return prefix + str(random.randint(1000000, 9999999))

def fmt(dt):
    return dt.strftime("%Y/%m/%d %H:%M:%S")

seq = 0
def gen_bill_no(special, apply_dt):
    # 特保单前缀 WF9897（当前唯一判定依据），普通单 WF7501
    code = "9897" if special else "7501"
    global seq
    seq += 1
    return f"WF{code}{apply_dt.strftime('%y%m%d')}{seq:06d}"

def make_emp_pair(prefix=None):
    p = prefix or random.choice(["H","F"])
    return gen_emp(p), random.choice(names)

TARGET_ROWS = 1200
start = datetime.datetime(2026, 8, 3, 7, 0, 0)
end = datetime.datetime(2026, 8, 8, 22, 0, 0)

def pick_status():
    r = random.random()
    if r < 0.55: return "arrived_ontime"          # 正常结案（到达且未超时、正常接收）
    if r < 0.67: return "arrived_late_release"    # 到达超时（流入门岗放行时已超时）
    if r < 0.75: return "arrived_recv_timeout"    # 已接收但接收时超时
    if r < 0.83: return "arrived_no_recv"         # 超时未接收（已放行、无接收时间、接收超时）
    return "in_transit"                            # 在途（其中约45%为在途超时）

stat_count = {}
bill_count = 0

while ws.max_row - 1 < TARGET_ROWS:
    # —— 整单固定属性：单据类型/物品分类（一单仅一种物品分类） ——
    special = random.random() < 0.18
    if special:
        item_type = random.choice(["新产品A级物料", "新产品机台"])
        item_class = item_type                      # 特保单分类仅两种
    else:
        item_type = "普通物品"
        item_class = random.choice(item_class_common)

    apply_dt = start + datetime.timedelta(seconds=random.randint(0, int((end-start).total_seconds())))
    bill_no = gen_bill_no(special, apply_dt)

    out_gate = gen_gate()
    in_gate = gen_gate()
    while in_gate == out_gate:
        in_gate = gen_gate()

    status = pick_status()
    stat_count[status] = stat_count.get(status, 0) + 1
    bill_count += 1

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
    remark = random.choice(["急件","試製","客退","返修","",""]) if random.random() < 0.5 else ""
    manager_id, manager_name = make_emp_pair("F")
    source = random.choice(["手動提單","系統自動","ERP同步"])
    customs = gen_emp("") if (special and random.random() < 0.5) else ""
    if random.random() < 0.3:
        conf_id, conf_name = make_emp_pair("H")
    else:
        conf_id, conf_name = "", ""

    # —— 门岗路径：流出门岗 →(中途门岗)→ 流入门岗（在途单不抵达流入门岗） ——
    arrived = status != "in_transit"
    path = [out_gate]
    k = random.randint(1, 2) if not arrived else random.randint(0, 2)
    for _ in range(k):
        g = gen_gate()
        while g in path or g == in_gate:
            g = gen_gate()
        path.append(g)
    if arrived:
        path.append(in_gate)

    release_times = []
    t = apply_dt + datetime.timedelta(minutes=random.randint(10, 180))
    for i in range(len(path)):
        release_times.append(t)
        t = t + datetime.timedelta(minutes=random.randint(30, 200))

    # —— 放行超时：到达超时单调整最后一笔时间使其超期；超时标记只打在最后一笔 ——
    deadline_arrival = apply_dt + datetime.timedelta(hours=12)
    if arrived:
        if status == "arrived_late_release":
            release_times[-1] = deadline_arrival + datetime.timedelta(hours=random.randint(1, 8))
        else:
            if release_times[-1] > deadline_arrival:
                release_times[-1] = deadline_arrival - datetime.timedelta(minutes=random.randint(10, 120))
    arrival_time = release_times[-1] if arrived else None
    in_transit_timeout = (not arrived) and random.random() < 0.45

    # —— 接收字段：仅最后一笔（接收发生在流入门岗） ——
    recv_id = recv_name = recv_dept = recv_time = recv_status = ""
    recv_timeout = "0"
    if status == "arrived_recv_timeout":        # 已接收但接收时超时
        recv_id, recv_name = make_emp_pair("H")
        recv_dept = random.choice(depts)
        recv_time = arrival_time + datetime.timedelta(hours=random.randint(3, 10))
        recv_status = "正常"
        recv_timeout = "1"
    elif status == "arrived_ontime":            # 正常接收
        recv_id, recv_name = make_emp_pair("H")
        recv_dept = random.choice(depts)
        recv_time = arrival_time + datetime.timedelta(minutes=random.randint(10, 90))
        recv_status = "正常"
    elif status == "arrived_no_recv":           # 超时未接收
        recv_status = "未接收"
        recv_timeout = "1"
    elif status == "arrived_late_release":      # 到达超时：部分已接收部分未接收
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
        # 超时标记只打在最后一笔记录（最后一笔决定整单状态）
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
