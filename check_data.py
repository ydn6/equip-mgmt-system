import psycopg2

conn = psycopg2.connect(
    database="postgres", user="ryan", password="ryan@123",
    host="192.168.31.160", port=5432
)
cur = conn.cursor()

# 统计行数
for table in ["workshop", "equipment", "maintenance"]:
    cur.execute(f"SELECT count(*) FROM {table}")
    print(f"{table:15s}  {cur.fetchone()[0]:>5} 条")

# 各表抽几条看看
print("\n--- workshop 样例 ---")
cur.execute("SELECT * FROM workshop LIMIT 3")
for r in cur.fetchall():
    print(r)

print("\n--- equipment 样例 ---")
cur.execute("SELECT equip_id, name, status, price FROM equipment LIMIT 3")
for r in cur.fetchall():
    print(r)

print("\n--- maintenance 样例 ---")
cur.execute("SELECT equip_id, maintenance_time, fault_desc, repair_cost FROM maintenance LIMIT 3")
for r in cur.fetchall():
    print(r)

cur.close()
conn.close()
