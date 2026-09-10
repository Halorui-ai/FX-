# -*- coding: utf-8 -*-
import random, datetime, openpyxl

random.seed(20260728)
BASE = r"C:\Users\Ray\OneDrive\文档\液态玻璃看板Qoder\物品放行监控_原备份.xlsx"

wb = openpyxl.load_workbook(BASE)
ws = wb.active
headers = [c.value for c in ws[1]]

# ---------- 基础数据池 ----------
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

def gen_emp(prefix):
    return prefix + str(random.randint(1000000, 9999999))

def gen_name():
    return random.choice(names)

def fmt(dt):
    return dt.strftime("%Y/%m/%d %H:%M:%S")

seq = 1
def gen_bill_no(item_type, apply_dt):
    code = "7501" if item_type == "普通物品" else "8888"
    ymd = apply_dt.strftime("%y%m%d")
    global seq
    seq += 1
    return f"WF{code}{ymd}{seq:06d}"

def make_emp_pair(prefix=None):
    p = prefix or random.choice(["H","F"])
    return gen_emp(p), gen_name()

# ---------- 生成单号 ----------
TARGET_ROWS = 1000  # 目标新增行数
start = datetime.datetime(2026, 7, 24, 7, 0, 0)
end = datetime.datetime(2026, 7, 28, 22, 0, 0)

# 状态分布: arrived_ontime / arrived_late_release / arrived_recv_timeout / in_transit
def pick_status():
    r = random.random()
    if r < 0.70: return "arrived_ontime"
    if r < 0.82: return "arrived_late_release"
    if r < 0.90: return "arrived_recv_timeout"
    return "in_transit"

stat_count = {"arrived_ontime":0,"arrived_late_release":0,"arrived_recv_timeout":0,"in_transit":0}
bill_count = 0

while ws.max_row - 1 < TARGET_ROWS:
    # 物品类型
    it_r = random.random()
    if it_r < 0.75:
        item_type = "普通物品"
    elif it_r < 0.90:
        item_type = "新产品A级物料"
    else:
        item_type = "新产品机台"

    # 申请时间
    apply_dt = start + datetime.timedelta(seconds=random.randint(0, int((end-start).total_seconds())))
    bill_no = gen_bill_no(item_type, apply_dt)

    # 流出/流入门岗
    out_gate = gen_gate()
    in_gate = gen_gate()
    while in_gate == out_gate:
        in_gate = gen_gate()

    status = pick_status()
    stat_count[status] += 1
    bill_count += 1

    # 申请人/携带人 (大多相同)
    app_id, app_name = make_emp_pair("H")
    app_dept = random.choice(depts)
    app_ext = str(random.randint(30000, 69999))
    if random.random() < 0.8:
        carry_id, carry_name, carry_dept, carry_ext = app_id, app_name, app_dept, app_ext
    else:
        carry_id, carry_name = make_emp_pair("H")
        carry_dept = random.choice(depts)
        carry_ext = str(random.randint(30000, 69999))

    # 物品分类
    if item_type == "新产品A级物料":
        item_class = "新产品A级物料"
    elif item_type == "新产品机台":
        item_class = "新产品机台"
    else:
        item_class = random.choice(item_class_common)

    model = random.choice(models) if (item_type != "普通物品" or random.random() < 0.5) else ""
    item_name = random.choice(item_names)
    item_cat = random.choice(item_cats)
    item_model = gen_emp("") if random.random() < 0.4 else ""  # 型号
    unit = random.choice(units)
    qty = random.randint(1, 500)
    item_id = str(random.randint(10000000, 39999999))
    remark = random.choice(["Del","","急件","試製","客退","返修","",""]) if random.random() < 0.5 else ""
    manager_id, manager_name = make_emp_pair("F")
    source = random.choice(["手動提單","系統自動","ERP同步"])
    customs = gen_emp("") if (item_type != "普通物品" and random.random() < 0.5) else ""
    if random.random() < 0.3:
        conf_id, conf_name = make_emp_pair("H")
    else:
        conf_id, conf_name = "", ""

    # 构建门岗路径
    if status == "in_transit":
        k = random.randint(1, 2)  # 中间门岗数
        path = [out_gate]
        for _ in range(k):
            g = gen_gate()
            while g in path or g == in_gate:
                g = gen_gate()
            path.append(g)
        arrived = False
    else:
        k = random.randint(0, 2)
        path = [out_gate]
        for _ in range(k):
            g = gen_gate()
            while g in path or g == in_gate:
                g = gen_gate()
            path.append(g)
        path.append(in_gate)  # 最后一站为流入门岗
        arrived = True

    # 各门岗放行时间(递增)
    release_times = []
    t = apply_dt + datetime.timedelta(minutes=random.randint(10, 180))
    for i in range(len(path)):
        release_times.append(t)
        t = t + datetime.timedelta(minutes=random.randint(30, 200))

    deadline_arrival = apply_dt + datetime.timedelta(hours=12)
    # 按状态校正到达时间, 使超时标记与状态一致
    if arrived:
        if status == "arrived_late_release":
            release_times[-1] = deadline_arrival + datetime.timedelta(hours=random.randint(1, 8))
        else:  # arrived_ontime / arrived_recv_timeout 均应按时到达
            if release_times[-1] > deadline_arrival:
                release_times[-1] = deadline_arrival - datetime.timedelta(minutes=random.randint(10, 120))
    arrival_time = release_times[-1] if arrived else None

    # 接收相关(仅到达后)
    recv_id = recv_name = recv_dept = recv_time = ""
    recv_status = ""
    recv_timeout = "0"

    for idx, gate in enumerate(path):
        is_last = (idx == len(path) - 1)
        # 放行人
        rel_id, rel_name = make_emp_pair("F")
        rel_dept = random.choice(depts)
        # 放行状态
        rel_status = "正常" if random.random() < 0.95 else "異常"
        # 放行超时: 仅末行有意义, 直接由状态决定以保证一致
        if is_last:
            if arrived:
                rel_timeout = "1" if status == "arrived_late_release" else "0"
            else:
                rel_timeout = "1"       # 在途,未按时到达
        else:
            rel_timeout = "0"

        # 末行且到达 -> 处理接收
        if is_last and arrived:
            recv_id, recv_name = make_emp_pair("H")
            recv_dept = random.choice(depts)
            recv_deadline = arrival_time + datetime.timedelta(hours=2)
            if status == "arrived_recv_timeout":
                recv_time = arrival_time + datetime.timedelta(hours=random.randint(3, 10))
                recv_status = "正常"
                recv_timeout = "1"
            elif status == "arrived_late_release":
                recv_time = arrival_time + datetime.timedelta(minutes=random.randint(10, 90))
                recv_status = "正常"
                recv_timeout = "0"
            else:  # arrived_ontime
                recv_time = arrival_time + datetime.timedelta(minutes=random.randint(10, 90))
                recv_status = "正常"
                recv_timeout = "0"

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
            "接收時間": fmt(recv_time) if recv_time else "",
            "接收超時": recv_timeout,
            "接收狀態": recv_status,
            "接收人工號": recv_id,
            "接收人姓名": recv_name,
            "接收人部門": recv_dept,
            "物品分類": item_class,
            "機種": model,
            "放行物品名稱": item_name,
            "放行物品分類": item_cat,
            "物品型號": item_model,
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
        # 按表头顺序输出
        ws.append([row.get(h, "") for h in headers])

TMP = r"C:\Users\Ray\OneDrive\文档\液态玻璃看板Qoder\物品放行监控_生成验证.xlsx"
wb.save(TMP)
print("完成. 总行数(含原表头+原1行):", ws.max_row)
print("新增行数:", ws.max_row - 2)
print("单号数:", bill_count)
print("状态分布:", stat_count)
# 校验: 在途单是否都无流入门岗匹配, 到达单是否都有
import collections
bill_rows = collections.defaultdict(list)
for r in range(3, ws.max_row + 1):
    bn = ws.cell(r, 2).value
    ag = ws.cell(r, 14).value
    ig = ws.cell(r, 13).value
    bill_rows[bn].append((ag, ig))
intransit_ok = 0; arrived_ok = 0
for bn, rows in bill_rows.items():
    igs = set(ig for _, ig in rows)
    ags = set(ag for ag, _ in rows)
    if igs and ags and igs.pop() in ags:
        arrived_ok += 1
    else:
        intransit_ok += 1
print("到达单(末站==流入):", arrived_ok, " 在途单(无匹配):", intransit_ok)
