import psycopg2

c = psycopg2.connect(
    database='postgres', user='ryan', password='ryan@123',
    host='192.168.31.160', port=5432
)
cur = c.cursor()

for t in ['workshop', 'equipment', 'maintenance']:
    print(f'\n=== {t} ===')
    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{t}' ORDER BY ordinal_position")
    for r in cur.fetchall():
        print(f'  {r[0]:25s} {r[1]}')
    cur.execute(f"SELECT * FROM {t} LIMIT 1")
    row = cur.fetchone()
    if row:
        print(f'  -> sample: {row}')

c.close()
