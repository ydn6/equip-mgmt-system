import psycopg2
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('zh_CN')
conn = psycopg2.connect(database="postgres", user="ryan", password="ryan@123", host="192.168.31.160", port=5432)
cur = conn.cursor()

# 先清空旧数据
cur.execute("DELETE FROM maintenance")
cur.execute("DELETE FROM equipment")
cur.execute("DELETE FROM workshop")

# 车间数据
workshops = [('W01','加工车间','厂区A'), ('W02','装配车间','厂区A'), ('W03','喷涂车间','厂区B'),
             ('W04','检验车间','厂区B'), ('W05','包装车间','厂区C')]
for w in workshops:
    cur.execute("INSERT INTO workshop VALUES (%s,%s,%s)", w)

# 生成50台设备
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
]
statuses = ['在用','维修中','报废']
equipment_ids = []
for i in range(1, 51):
    eid = f'EQ{i:04d}'
    name = equipment_names[i - 1]
    model = f'MOD-{random.randint(100,999)}'
    manu_date = fake.date_between(start_date='-10y', end_date='-1y')
    price = round(random.uniform(5000, 500000), 2)
    ws = random.choice(workshops)[0]
    person = fake.name()
    status = random.choices(statuses, weights=[70,20,10])[0]
    cur.execute("INSERT INTO equipment VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (eid, name, model, manu_date, price, ws, person, status))
    equipment_ids.append(eid)

# 生成300条维修记录
faults = ['主轴异响','电路故障','传感器失灵','润滑不足','过载停机','正常磨损','异物堵塞']
for _ in range(300):
    eid = random.choice(equipment_ids)
    days_ago = random.randint(0, 365*2)
    maint_time = datetime.now() - timedelta(days=days_ago)
    fault = random.choice(faults)
    cost = round(random.uniform(200, 15000), 2)
    cur.execute("INSERT INTO maintenance (equip_id, maintenance_time, fault_desc, repair_cost) VALUES (%s,%s,%s,%s)",
                (eid, maint_time, fault, cost))

conn.commit()
cur.close()
conn.close()
print("模拟数据插入成功！")