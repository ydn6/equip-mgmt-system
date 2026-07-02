import psycopg2

c = psycopg2.connect(
    database='postgres', user='ryan', password='ryan@123',
    host='192.168.31.160', port=5432
)
cur = c.cursor()

cur.execute("SELECT COUNT(*) FROM maintenance")
print('Total maintenance:', cur.fetchone()[0])

cur.execute("""
    SELECT equip_id, COUNT(*) c FROM maintenance
    GROUP BY equip_id ORDER BY c DESC LIMIT 5
""")
print('Top 5 devices:')
for r in cur.fetchall():
    print(f'  {r[0]} -> {r[1]} records')

cur.execute("""
    SELECT TO_CHAR(maintenance_time,'YYYY-MM') m, COUNT(*) c
    FROM maintenance
    WHERE equip_id = (
        SELECT equip_id FROM maintenance
        GROUP BY equip_id ORDER BY COUNT(*) DESC LIMIT 1
    )
    GROUP BY m ORDER BY m
""")
print('Top device monthly trend:')
for r in cur.fetchall():
    print(f'  {r[0]} -> {r[1]} 次')

c.close()
