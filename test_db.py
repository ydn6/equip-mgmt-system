import psycopg2

try:
    conn = psycopg2.connect(
        host="192.168.31.160",
        port=5432,
        database="postgres",
        user="ryan",
        password="ryan@123"
    )
    print("连接成功！")

    cur = conn.cursor()

    # ---- 测试查询 ----
    # 1. 查看数据库版本
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"数据库版本: {version}")

    # 2. 查看当前数据库
    cur.execute("SELECT current_database();")
    db_name = cur.fetchone()[0]
    print(f"当前数据库: {db_name}")

    # 3. 查看所有用户表
    cur.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY tablename;
    """)
    tables = cur.fetchall()
    if tables:
        print(f"用户表 ({len(tables)} 张):")
        for t in tables:
            print(f"  - {t[0]}")
    else:
        print("当前数据库中没有用户表。")

    cur.close()
    conn.close()
    print("连接已关闭。")

except psycopg2.OperationalError as e:
    print(f"连接失败: {e}")
except Exception as e:
    print(f"出错: {e}")
