# -*- coding: utf-8 -*-
# 物品放行监控 大数据量模拟生成 (~10万行) - write_only 高性能版
import random, datetime, openpyxl
from openpyxl.utils import get_column_letter

random.seed(20260729)
OUT = r"C:\Users\Ray\OneDrive\文档\液态玻璃看板Qoder\物品放行监控_生成_100k.xlsx"
TARGET = 100000

headers = [
    "申請日期","放行單號","物品類型","申請人工號","申請人姓名","申請人部門","申請人分機",
    "實際攜帶人工號","實際攜帶人姓名","實際攜帶人部門","實際攜帶人分機",
    "放行單流出門崗","放行單流入門崗","實際放行門崗","放行人工號","放行人姓名",
    "實際放行時間","放行狀態","放行超時","接收時間","接收超時","接收狀態",
    "接收人工號","接收人姓名","接收人部門","物品分類","機種","放行物品名稱","放行物品分類",
    "物品型號","放行單位","放行數量","物品ID","物品信息備註","廠區","簽核權限主管",
    "資料來源","報關單號","確認人工號","確認人姓名"
]
NCOL = len(headers)

names = ["劉斌","周勇","趙飛","張巧莉","郝強","馬萬玉","王偉","李娜","陳靜","楊帆",
         "黃磊","吳婷","鄭浩","孫琳","朱軍","胡敏","郭強","林芳","何勇","高翔",
         "劉洋","徐麗","羅傑","梁爽","宋佳","唐磊","韓雪","馮濤","董潔","曹宇",
         "彭勇","蕭雅","袁泉","潘磊","蔡明","余華","杜峰","葉青","蘇陽","魏晨",
         "范冰","石磊","譚維","賈玲","夏雨","汪峰","盧俊","蔣雯","丁俊","方圓"]
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
item_cats = ["主板","網卡","耗材","包材","設備","模組","機台","五金","電子件","結構件"]
units = ["PCS","BOX","KG","SET","LOT","ROLL"]
item_class_common = ["生產物料(非A類)","耗材","资讯物品","设备"]

def gen_gate():
    return f"ZZ-{random.choice(zones)}{random.choice(buildings)}-{random.choice(floors)}-{random.choice(gate_names)}"

def make_emp_pair(prefix=None):
    p = prefix or random.choice(["H","F"])
    return f"{p}{random.randint(1000000,9999999)}", random.choice(names)

def fmt(dt):
    return dt.strftime("%Y/%m/%d %H:%M:%S")

seq = 0
def gen_bill_no(prefix, d):
    global seq
    seq += 1
    return f"{prefix}{d.strftime('%y%m%d')}{seq:06d}"

now = datetime.datetime.now()
end = now
start = now - datetime.timedelta(days=7)
span = int((end - start).total_seconds())
def rand_dt():
    return start + datetime.timedelta(seconds=random.randint(0, span))

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "物品放行监控"
# 首行: 合并空白单元格横跨所有表头列
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=NCOL)
# 占位首行(不append, 避免空行占用row2)
for c in range(1, NCOL + 1):
    ws.cell(row=1, column=c, value=None)
ws.append(headers)              # 第2行表头

stat_count = {"A_normal":0,"B_rel_late":0,"C_transit_ok":0,"D_transit_to":0,"E_recv_to_norecv":0,"F_recv_to_recv":0}
rows = 0
while rows < TARGET:
    is_special = random.random() < 0.25
    if is_special:
        prefix = "WF9897"
        item_type = random.choice(["新产品A级物料","新产品机台"])
    else:
        prefix = "WF7501"
        item_type = "普通物品"

    apply_dt = rand_dt()
    bill_no = gen_bill_no(prefix, apply_dt)
    out_gate = gen_gate()
    in_gate = gen_gate()
    while in_gate == out_gate:
        in_gate = gen_gate()

    status = random.choices(["A","B","C","D","E","F"], weights=[50,12,12,10,8,8])[0]
    stat_count[{"A":"A_normal","B":"B_rel_late","C":"C_transit_ok","D":"D_transit_to",
                "E":"E_recv_to_norecv","F":"F_recv_to_recv"}[status]] += 1
    arrived = status in ("A","B","E","F")

    if arrived:
        k = random.randint(0, 2)
        path = [out_gate]
        for _ in range(k):
            g = gen_gate()
            while g in path or g == in_gate:
                g = gen_gate()
            path.append(g)
        path.append(in_gate)
    else:
        k = random.randint(1, 2)
        path = [out_gate]
        for _ in range(k):
            g = gen_gate()
            while g in path or g == in_gate:
                g = gen_gate()
            path.append(g)

    release_times = []
    t = apply_dt + datetime.timedelta(minutes=random.randint(10, 180))
    for i in range(len(path)):
        release_times.append(t)
        t += datetime.timedelta(minutes=random.randint(30, 200))
    deadline_arrival = apply_dt + datetime.timedelta(hours=12)
    if arrived:
        if status == "B":
            release_times[-1] = deadline_arrival + datetime.timedelta(hours=random.randint(1, 8))
        else:
            if release_times[-1] > deadline_arrival:
                release_times[-1] = deadline_arrival - datetime.timedelta(minutes=random.randint(10, 120))
    arrival_time = release_times[-1] if arrived else None

    app_id, app_name = make_emp_pair("H")
    app_dept = random.choice(depts)
    app_ext = str(random.randint(30000, 69999))
    if random.random() < 0.8:
        carry_id, carry_name, carry_dept, carry_ext = app_id, app_name, app_dept, app_ext
    else:
        carry_id, carry_name = make_emp_pair("H")
        carry_dept = random.choice(depts)
        carry_ext = str(random.randint(30000, 69999))

    item_class = item_type if is_special else random.choice(item_class_common)
    model = random.choice(models) if (is_special or random.random() < 0.5) else ""
    item_name = random.choice(item_names)
    item_cat = random.choice(item_cats)
    item_model = (f"M{random.randint(100000,999999)}" if random.random() < 0.4 else "")
    unit = random.choice(units)
    qty = random.randint(1, 500)
    item_id = str(random.randint(10000000, 39999999))
    remark = random.choice(["Del","","急件","試製","客退","返修","",""]) if random.random() < 0.5 else ""
    manager_id, manager_name = make_emp_pair("F")
    source = random.choice(["手動提單","系統自動","ERP同步"])
    customs = (f"C{random.randint(100000,999999)}" if (is_special and random.random() < 0.5) else "")
    if random.random() < 0.3:
        conf_id, conf_name = make_emp_pair("H")
    else:
        conf_id, conf_name = "", ""

    recv_id = recv_name = recv_dept = recv_time = recv_status = ""
    recv_timeout = "0"
    if arrived:
        if status == "E":
            recv_timeout = "1"
        elif status == "F":
            recv_id, recv_name = make_emp_pair("H")
            recv_dept = random.choice(depts)
            recv_time = arrival_time + datetime.timedelta(hours=random.randint(3, 10))
            recv_status = "正常"
            recv_timeout = "1"
        else:
            recv_id, recv_name = make_emp_pair("H")
            recv_dept = random.choice(depts)
            recv_time = arrival_time + datetime.timedelta(minutes=random.randint(10, 90))
            recv_status = "正常"
            recv_timeout = "0"

    for idx, gate in enumerate(path):
        is_last = (idx == len(path) - 1)
        rel_id, rel_name = make_emp_pair("F")
        rel_status = "正常" if random.random() < 0.95 else "異常"
        if is_last:
            if arrived:
                rel_timeout = "1" if status == "B" else "0"
            else:
                rel_timeout = "1" if status == "D" else "0"
        else:
            rel_timeout = "0"

        ws.append([
            fmt(apply_dt), bill_no, item_type, app_id, app_name, app_dept, app_ext,
            carry_id, carry_name, carry_dept, carry_ext,
            out_gate, in_gate, gate, rel_id, rel_name,
            fmt(release_times[idx]), rel_status, rel_timeout,
            fmt(recv_time) if recv_time else "", recv_timeout, recv_status,
            recv_id, recv_name, recv_dept, item_class, model, item_name, item_cat,
            item_model, unit, qty, item_id, remark, "鄭州", manager_id,
            source, customs, conf_id, conf_name
        ])
        rows += 1
        if rows % 10000 == 0:
            print(f"已生成 {rows} 行...")

wb.save(OUT)
print("生成完成 ->", OUT)
print("数据行数:", rows, " 单号数:", seq)
print("状态分布(按单):", stat_count)
