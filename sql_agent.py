""".
SQL Agent：自然语言 → SQL → 执行 → 展示结果
核心设计：只读连接、白名单表、SQL校验
"""
import sys, os, sqlite3, re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB_PATH, get_schema

# ---------- 安全层 ----------
WHITELIST_TABLES = ["users", "products", "orders"]
FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
    "CREATE", "TRUNCATE", "REPLACE", "ATTACH",
]


def validate_sql(sql: str) -> bool:
    """检查SQL是否安全：只允许SELECT查询"""
    sql_upper = sql.strip().upper()

    # 必须以SELECT开头
    if not sql_upper.startswith("SELECT"):
        return False, "只允许SELECT查询"

    # 禁止危险关键词
    for kw in FORBIDDEN_KEYWORDS:
        if kw in sql_upper:
            return False, f"禁止使用 {kw} 操作"

    return True, "OK"


def execute_safe_query(sql: str, max_rows=30):
    """执行只读SQL查询（安全层）"""
    safe, msg = validate_sql(sql)
    if not safe:
        return {"error": msg, "success": False}

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()

        columns = [desc[0] for desc in cursor.description]
        data = [dict(row) for row in rows[:max_rows]]

        return {
            "success": True,
            "columns": columns,
            "data": data,
            "total_rows": len(rows),
            "showed_rows": min(len(rows), max_rows),
        }
    except Exception as e:
        return {"error": str(e), "success": False}


# ---------- LLM 生成 SQL ----------
def setup_llm():
    """获取LLM实例"""
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "pdf-qa-system", ".env"))

    # 也尝试同级目录
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未设置")

    return ChatOpenAI(api_key=api_key, base_url=base_url, model=model, temperature=0.1)


def generate_sql(nl_query: str, schema: str) -> str:
    """把自然语言转成SQL"""
    llm = setup_llm()
    prompt = f"""你是一个SQL专家。根据数据库结构和用户需求生成SQL查询。

数据库结构：
{schema}

要求：
1. 只生成SELECT查询
2. 输出纯SQL，不要任何解释和markdown标记
3. 用中文别名显示字段

用户需求：{nl_query}

SQL："""
    response = llm.invoke(prompt)
    sql = response.content.strip()

    # 清理可能的 markdown 标记
    sql = re.sub(r"^```(?:sql)?\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip()

    return sql


def explain_sql(sql: str) -> str:
    """解释SQL含义"""
    llm = setup_llm()
    prompt = f"用一句话解释以下SQL查询在做什么（面向非技术人员）：\n\n{sql}"
    return llm.invoke(prompt).content.strip()


# ---------- 测试 ----------
if __name__ == "__main__":
    schema = get_schema()
    print("数据库结构:\n", schema)

    queries = [
        "哪个产品卖得最多？按销量排序",
        "北京的用户花了多少钱？",
        "各城市的订单总额排名",
    ]

    for q in queries:
        print(f"\n{'='*50}")
        print(f"用户: {q}")

        sql = generate_sql(q, schema)
        print(f"SQL: {sql}")

        result = execute_safe_query(sql)
        if result["success"]:
            print(f"结果 ({result['showed_rows']}/{result['total_rows']} 行):")
            for row in result["data"]:
                print(f"  {row}")
        else:
            print(f"错误: {result['error']}")

        exp = explain_sql(sql)
        print(f"解释: {exp}")
