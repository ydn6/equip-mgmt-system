"""完整重建数据库：100台设备 (ID 001-100) + 维修记录"""
import psycopg2
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('zh_CN')
conn = psycopg2.connect(
    database="postgres", user="ryan", password="ryan@123",
    host="192.168.31.160", port=5432
)
cur = conn.cursor()

# ==== 清空 =====
cur.execute("DELETE FROM maintenance")
cur.execute("DELETE FROM equipment")
cur.execute("DELETE FROM workshop")
print("旧数据已清除")

# ==== 车间 =====
workshops = [
    ('W01', '加工车间', '厂区A'),
    ('W02', '装配车间', '厂区A'),
    ('W03', '喷涂车间', '厂区B'),
    ('W04', '检验车间', '厂区B'),
    ('W05', '包装车间', '厂区C'),
]
for w in workshops:
    cur.execute("INSERT INTO workshop VALUES (%s,%s,%s)", w)
print("车间已插入: 5")

# ==== 设备 ===== (100 台, ID: 001~100)
equipment_names = [
    '数控车床', '立式加工中心', '卧式铣床', '平面磨床', '外圆磨床',
    '摇臂钻床', '剪板机', '折弯机', '液压冲床', '激光切割机',
    '电火花线切割机', '注塑机', '压铸机', '滚齿机', '插齿机',
    '镗床', '龙门刨床', '带锯床', '焊接机器人', '喷涂机器人',
    'AGV搬运车', '自动贴片机', '回流焊炉', '波峰焊机', '三坐标测量仪',
    '硬度计', '拉力试验机', '动平衡机', '超声波清洗机', '空压机',
    '冷水机组', '变压器', '发电机组', '螺杆挤出机', '吹塑机',
    '切管机', '弯管机', '抛光机', '喷砂机', '烘箱',
    '真空镀膜机', '光刻机', '蚀刻机', '离子注入机', '化学气相沉积设备',
    '贴标机', '灌装机', '封口机', '码垛机器人', '缠绕包装机',
    # 新增 50 种设备名
    '数控磨床', '高速冲床', '自动拧紧机', '激光打标机', '超声波焊接机',
    '热压机', '冷压机', '涂胶机器人', '自动检测线', '气密性测试仪',
    '振动试验台', '高低温试验箱', '盐雾试验机', '万能试验机', '光谱分析仪',
    '三坐标划线机', '自动铆接机', '旋铆机', '压装机', '感应加热设备',
    '中频炉', '高频淬火机床', '渗碳炉', '氮化炉', '真空热处理炉',
    '喷丸机', '清洗烘干线', '自动包装线', '码垛机', '缠绕机',
    '自动称重机', '金属检测机', 'X光检测仪', '视觉检测系统', '激光测距仪',
    '红外热像仪', '振动分析仪', '油液分析仪', '颗粒计数器', '粗糙度仪',
    '圆柱度仪', '圆度仪', '轮廓仪', '投影仪', '影像测量仪',
    '自动上下料机', '桁架机械手', '关节机器人', '协作机器人', 'SCARA机器人',
]

statuses = ['未使用', '在用', '维修中', '报废']
status_weights = [10, 55, 25, 10]
equip_ids = []

for i in range(1, 101):
    eid = f'{i:03d}'
    name = equipment_names[i - 1]
    model = f'MOD-{random.randint(100, 999)}'
    manu_date = fake.date_between(start_date='-10y', end_date='-1y')
    price = round(random.uniform(5000, 500000), 2)
    ws = random.choice(workshops)[0]
    person = fake.name()
    status = random.choices(statuses, weights=status_weights, k=1)[0]

    cur.execute(
        "INSERT INTO equipment VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (eid, name, model, manu_date, price, ws, person, status)
    )
    equip_ids.append(eid)

print(f"设备已插入: {len(equip_ids)}")

# ==== 维修记录 =====
faults = [
    '主轴异响', '电路故障', '传感器失灵', '润滑不足', '过载停机',
    '正常磨损', '异物堵塞', '液压泄漏', '冷却系统故障', '传动皮带断裂',
    '轴承过热', '电机烧毁', '控制面板失灵', '气路堵塞', '刀片磨损',
    '接地不良', '电源模块故障', '通讯中断', '限位开关损坏', '密封圈老化',
]
fault_weights = [12, 10, 9, 8, 7, 15, 6, 5, 6, 4, 5, 2, 4, 3, 8, 3, 3, 5, 4, 6]

end_date = datetime.now()
start_date = end_date - timedelta(days=730)
total_maint = 0

# 只为"在用"和"维修中"的设备生成维修记录
active_ids = [eid for eid, st in zip(equip_ids, [random.choices(statuses, weights=status_weights, k=1)[0] for _ in range(100)])]
# 重新获取实际状态
cur.execute("SELECT equip_id FROM equipment WHERE status IN ('在用','维修中')")
active_ids = [r[0] for r in cur.fetchall()]
print(f"有维修记录的设备: {len(active_ids)} 台")

for eid in active_ids:
    record_count = random.randint(5, 70)
    first_maint = start_date + timedelta(days=random.randint(0, 365))

    for _ in range(record_count):
        days_offset = random.randint(0, max(1, (end_date - first_maint).days))
        maint_time = first_maint + timedelta(days=days_offset)

        # 30% 概率把部分记录集中在近 4 个月，形成上升趋势
        if random.random() < 0.3:
            maint_time = end_date - timedelta(days=random.randint(0, 120))

        fault = random.choices(faults, weights=fault_weights, k=1)[0]
        cost = round(random.uniform(200, 20000), 2)

        cur.execute(
            "INSERT INTO maintenance (equip_id, maintenance_time, fault_desc, repair_cost) VALUES (%s,%s,%s,%s)",
            (eid, maint_time, fault, cost)
        )
        total_maint += 1

conn.commit()

# ==== 统计 =====
cur.execute("SELECT COUNT(*) FROM equipment")
eq_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM maintenance")
m_count = cur.fetchone()[0]
cur.execute("SELECT status, COUNT(*) FROM equipment GROUP BY status ORDER BY status")
st_counts = cur.fetchall()

cur.close()
conn.close()

print(f"\n===== 数据重建完成 =====")
print(f"设备总数: {eq_count}")
print(f"维修记录: {m_count}")
for st, cnt in st_counts:
    print(f"  {st}: {cnt} 台")
