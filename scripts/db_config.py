import psycopg2
from psycopg2 import sql

# 数据库连接参数
db_config = {
    'dbname': 'your_database_name',
    'user': 'your_username',
    'password': 'your_password',
    'host': 'your_database_host',  # 云端数据库的主机名
    'port': '5432',  # PostgreSQL 默认端口
    'sslmode': 'require'  # 启用 SSL/TLS 加密
}

# 连接到数据库
try:
    connection = psycopg2.connect(**db_config)
    cursor = connection.cursor()

    # 设置连接超时
    connection.set_session(autocommit=True)

    # 执行初始化脚本
    cursor.execute(sql.SQL("CREATE TABLE IF NOT EXISTS example_table (id SERIAL PRIMARY KEY, name VARCHAR(100));"))

    print("Database initialized successfully.")

except Exception as error:
    print(f"Error connecting to the database: {error}")

finally:
    if connection:
        cursor.close()
        connection.close()