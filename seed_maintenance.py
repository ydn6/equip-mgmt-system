"""插入大量维修记录，形成有明显趋势的数据"""
import psycopg2
import random
from datetime import datetime, timedelta

conn = psycopg2.connect(
    database="postgres", user="ryan", password="ryan@123",
    host="192.168.31.160", port=5432
)
cur = conn.cursor()

# 获取所有设备ID（排除未使用的设备）
cur.execute("SELECT equip_id, status FROM equipment WHERE status IN ('在用', '维修中')")
equipment = cur.fetchall()
equip_ids = [e[0] for e in equipment]

faults = [
    '主轴异响', '电路故障', '传感器失灵', '润滑不足', '过载停机',
    '正常磨损', '异物堵塞', '液压泄漏', '冷却系统故障', '传动皮带断裂',
    '轴承过热', '电机烧毁', '控制面板失灵', '气路堵塞', '刀片磨损',
    '接地不良', '电源模块故障', '通讯中断', '限位开关损坏', '密封圈老化',
]

fault_weights = [12, 10, 9, 8, 7, 15, 6, 5, 6, 4, 5, 2, 4, 3, 8, 3, 3, 5, 4, 6]

# 时间范围：过去 24 个月
end_date = datetime.now()
start_date = end_date - timedelta(days=730)

total = 0
for eid in equip_ids:
    # 每台设备随机 10~80 条维修记录（形成不同密度）
    record_count = random.randint(10, 80)
    # 设备首次维修时间（最近 24 个月内随机起点）
    first_maint = start_date + timedelta(days=random.randint(0, 365))

    for _ in range(record_count):
        # 时间逐渐向现在靠近，形成"越近越密"的趋势
        days_offset = random.randint(0, max(1, (end_date - first_maint).days))
        maint_time = first_maint + timedelta(days=days_offset)

        # 偶尔让近期月份更密集
        if random.random() < 0.3:
            maint_time = end_date - timedelta(days=random.randint(0, 120))

        fault = random.choices(faults, weights=fault_weights, k=1)[0]
        cost = round(random.uniform(200, 20000), 2)

        cur.execute("""
            INSERT INTO maintenance (equip_id, maintenance_time, fault_desc, repair_cost)
            VALUES (%s, %s, %s, %s)
        """, (eid, maint_time, fault, cost))
        total += 1

conn.commit()
cur.close()
conn.close()
print(f"已插入 {total} 条维修记录")
