"""
补5: MCP 协议学习 — 用 FastMCP 创建工具服务器
概念：MCP (Model Context Protocol) 是 AI 应用连接外部工具的标准协议
三大原语：Tool（执行操作）、Resource（暴露数据）、Prompt（提示模板）

对比之前学的 Agent：
  - Agent 演示了「LLM决定调什么工具」的思想
  - MCP 把这个思想标准化了：任何 MCP 客户端都能用你的工具
"""
import sys, os

# 切换到脚本所在目录（确保能找到 database）
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

# ====== 创建 MCP 服务器 ======
mcp = FastMCP("SQL-Agent MCP Server")


# ====== 1. Resource：暴露数据（只读） ======
@mcp.resource("schema://database")
def get_database_schema() -> str:
    """获取销售数据库的表结构"""
    from database import get_schema
    return get_schema()


@mcp.resource("config://app")
def get_app_config() -> str:
    """获取服务器配置信息"""
    return (
        "SQL Agent MCP Server\n"
        "功能：查询销售数据库、数学计算\n"
        "数据库：SQLite (sales.db)\n"
        "表：users(用户), products(产品), orders(订单)"
    )


# ====== 2. Tool：执行操作 ======
@mcp.tool()
def calculator(expression: str) -> str:
    """计算数学表达式，如 '25 * 4 + 100' 或 '15800 * 0.85'"""
    try:
        allowed = {"abs": abs, "max": max, "min": min, "round": round}
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


@mcp.tool()
def query_sales_db(question: str) -> str:
    """用自然语言查询销售数据库，如'哪个产品卖得最多'"""
    from sql_agent import generate_sql, execute_safe_query, get_schema

    schema = get_schema()
    sql = generate_sql(question, schema)
    result = execute_safe_query(sql)

    if result["success"]:
        rows = result["data"]
        if not rows:
            return "查询结果为空"
        # 格式化输出
        headers = list(rows[0].keys())
        lines = [",  ".join(f"{k}={v}" for k, v in row.items()) for row in rows]
        return f"共 {len(rows)} 行结果：\n" + "\n".join(lines)
    return f"查询失败: {result['error']}"


@mcp.tool()
def get_table_data(table_name: str, limit: int = 10) -> str:
    """直接查询数据库表内容。支持的表：users, products, orders"""
    import sqlite3
    from database import DB_PATH

    allowed_tables = {"users", "products", "orders"}
    if table_name not in allowed_tables:
        return f"不允许查询表 '{table_name}'，支持的表: {allowed_tables}"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not rows:
        return "表为空"
    headers = list(rows[0].keys())
    lines = [",  ".join(f"{k}={v}" for k, v in row.items()) for row in rows]
    return "\n".join(lines)


# ====== 3. Prompt：提示模板 ======
@mcp.prompt()
def sales_analysis_prompt(question: str) -> str:
    """分析销售数据的提示模板"""
    return (
        f"你是一个销售数据分析助手。用户的问题是：{question}\n\n"
        "你可以使用以下工具：\n"
        "1. query_sales_db - 用自然语言查询数据库\n"
        "2. get_table_data - 查看表内容（users, products, orders）\n"
        "3. calculator - 做数学计算\n\n"
        "请根据数据给出分析结果。"
    )


# ====== 运行 ======
if __name__ == "__main__":
    print("=" * 60)
    print("MCP 服务器启动")
    print("=" * 60)
    print()
    print("可用资源:")
    print("  schema://database   - 数据库结构")
    print("  config://app        - 服务器配置")
    print()
    print("可用工具:")
    print("  calculator(expression)     - 数学计算")
    print("  query_sales_db(question)   - 自然语言查数据库")
    print("  get_table_data(table,limit)- 查看表内容")
    print()
    print("可用提示:")
    print("  sales_analysis_prompt      - 销售分析提示模板")
    print()
    print("启动方式:")
    print("  开发模式: mcp dev 07_mcp_server.py")
    print("  安装到Claude: mcp install 07_mcp_server.py")
    print("  直接运行: python 07_mcp_server.py")
    print()

    # 默认使用 stdio 传输
    mcp.run(transport="stdio")
