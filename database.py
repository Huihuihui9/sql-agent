import sqlite3
import os

DB_PATH = "data/sales.db"


def create_database():
    """创建示例数据库：电商销售数据"""
    os.makedirs("data", exist_ok=True)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 用户表
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            city TEXT,
            register_date TEXT
        )
    """)

    # 产品表
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL,
            stock INTEGER
        )
    """)

    # 订单表
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total_amount REAL,
            order_date TEXT,
            status TEXT
        )
    """)

    # 插入示例数据
    users = [
        (1, "张三", 28, "北京", "2024-01-15"),
        (2, "李四", 35, "上海", "2024-02-20"),
        (3, "王五", 24, "深圳", "2024-03-10"),
        (4, "赵六", 31, "杭州", "2024-01-05"),
        (5, "钱七", 27, "北京", "2024-04-01"),
        (6, "孙八", 29, "上海", "2024-03-15"),
        (7, "周九", 26, "深圳", "2024-05-20"),
        (8, "吴十", 33, "广州", "2024-02-01"),
    ]
    cursor.executemany("INSERT INTO users VALUES (?,?,?,?,?)", users)

    products = [
        (1, "MacBook Pro", "电子产品", 14999, 50),
        (2, "iPhone 15", "电子产品", 7999, 100),
        (3, "机械键盘", "配件", 599, 200),
        (4, "4K显示器", "配件", 2999, 80),
        (5, "Python编程书", "图书", 89, 500),
        (6, "AI入门指南", "图书", 59, 300),
        (7, "无线鼠标", "配件", 199, 150),
        (8, "降噪耳机", "配件", 999, 120),
    ]
    cursor.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)

    orders = [
        (1, 1, 1, 1, 14999, "2024-06-01", "已完成"),
        (2, 1, 3, 2, 1198, "2024-06-01", "已完成"),
        (3, 2, 2, 1, 7999, "2024-06-05", "已完成"),
        (4, 2, 8, 1, 999, "2024-06-05", "已完成"),
        (5, 3, 5, 3, 267, "2024-06-10", "已完成"),
        (6, 4, 4, 1, 2999, "2024-06-12", "已完成"),
        (7, 4, 6, 2, 118, "2024-06-12", "已完成"),
        (8, 5, 2, 1, 7999, "2024-06-15", "已完成"),
        (9, 5, 7, 1, 199, "2024-06-15", "已完成"),
        (10, 6, 1, 1, 14999, "2024-06-20", "已完成"),
        (11, 6, 8, 1, 999, "2024-06-20", "已完成"),
        (12, 7, 5, 2, 178, "2024-07-01", "待发货"),
        (13, 7, 6, 1, 59, "2024-07-01", "待发货"),
        (14, 8, 3, 1, 599, "2024-07-03", "待发货"),
    ]
    cursor.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?)", orders)

    conn.commit()
    conn.close()
    print(f"数据库已创建: {DB_PATH}")


def get_schema():
    """返回数据库结构描述"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    schema = []
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for table in tables:
        name = table[0]
        cursor.execute(f"PRAGMA table_info({name})")
        columns = cursor.fetchall()
        cols_desc = [f"{col[1]} ({col[2]})" for col in columns]
        schema.append(f"- 表 {name}: {', '.join(cols_desc)}")

    conn.close()
    return "\n".join(schema)


if __name__ == "__main__":
    create_database()
    print("\n数据库结构:")
    print(get_schema())
