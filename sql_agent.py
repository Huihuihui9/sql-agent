"""
SQL Agent：自然语言 → SQL → 执行 → 展示结果
核心设计：只读连接、白名单表、SQL校验、错误自动重试
v2.0 新增：结构化输出、SQL自动修正重试、统一 .env 加载、中文提示
"""
import sys
import os
import sqlite3
import re
import json

sys.stdout.reconfigure(encoding='utf-8')

from database import DB_PATH, get_schema

# ---------- LLM 配置 ----------
def setup_llm(temperature=0.1):
    """获取LLM实例，优先加载 sql-agent 自己目录下的 .env"""
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI

    # 优先加载当前项目目录下的 .env
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    else:
        load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未设置，请检查 .env 文件")

    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
    )


# ---------- 安全层 ----------
WHITELIST_TABLES = ["users", "products", "orders"]
FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
    "CREATE", "TRUNCATE", "REPLACE", "ATTACH", "DETACH",
]


def validate_sql(sql: str):
    """检查SQL是否安全：只允许SELECT查询，返回 (is_valid, message)"""
    sql_upper = sql.strip().upper()

    if not sql_upper.startswith("SELECT"):
        return False, "只允许SELECT查询"

    for kw in FORBIDDEN_KEYWORDS:
        # 单词边界匹配，避免误判 SELECT 里的字段名
        if re.search(r"\b" + kw + r"\b", sql_upper):
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
        columns = [desc[0] for desc in cursor.description]
        conn.close()

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


# ---------- LLM 生成 SQL（带自动重试） ----------
def generate_sql(nl_query: str, schema: str) -> str:
    """把自然语言转成 SQL（单次生成，不带重试）"""
    llm = setup_llm()
    prompt = f"""你是一个SQL专家。根据数据库结构和用户需求生成SQL查询。

数据库结构：
{schema}

要求：
1. 只生成SELECT查询，禁止使用任何写操作（INSERT/UPDATE/DELETE/DROP等）
2. 输出纯SQL，不要任何解释、注释和markdown标记
3. 用中文别名显示字段（AS 中文名）
4. 如果涉及金额，需要 JOIN users 和 orders 表
5. 日期字段是 TEXT 类型，格式为 'YYYY-MM-DD'

用户需求：{nl_query}

SQL："""
    response = llm.invoke(prompt)
    sql = response.content.strip()

    # 清理可能的 markdown 标记
    sql = re.sub(r"^```(?:sql)?\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip()

    return sql


def generate_sql_with_retry(nl_query: str, schema: str, max_retries: int = 2):
    """带自动重试的 SQL 生成：执行失败时让 LLM 修复错误

    Returns:
        dict: {
            "sql": str,
            "success": bool,
            "result": dict | None,   # execute_safe_query 的结果
            "retries": int,          # 重试次数
            "final_error": str | None,
        }
    """
    sql = generate_sql(nl_query, schema)
    retries = 0

    while True:
        result = execute_safe_query(sql)
        if result["success"]:
            return {
                "sql": sql,
                "success": True,
                "result": result,
                "retries": retries,
                "final_error": None,
            }

        error_msg = result["error"]

        if retries >= max_retries:
            return {
                "sql": sql,
                "success": False,
                "result": result,
                "retries": retries,
                "final_error": error_msg,
            }

        # 让 LLM 根据错误信息修正 SQL
        llm = setup_llm()
        retry_prompt = f"""之前生成的SQL有错误，请修正。

数据库结构：
{schema}

用户需求：{nl_query}

错误的SQL：{sql}

错误信息：{error_msg}

要求：
1. 只输出修正后的纯SQL，不要任何解释
2. 必须是SELECT查询
3. 注意表名和字段名必须和数据库结构完全一致

修正后的SQL："""
        response = llm.invoke(retry_prompt)
        sql = response.content.strip()
        sql = re.sub(r"^```(?:sql)?\s*", "", sql)
        sql = re.sub(r"\s*```$", "", sql)
        sql = sql.strip()
        retries += 1


def explain_sql(sql: str, nl_query: str = "") -> str:
    """解释SQL含义（中文，面向非技术人员）"""
    llm = setup_llm()
    context = f"\n用户原始问题：{nl_query}" if nl_query else ""
    prompt = f"用一句话解释以下SQL查询在做什么，面向非技术人员，用中文回答：{context}\n\nSQL：{sql}"
    return llm.invoke(prompt).content.strip()


# ---------- 结构化输出（Pydantic） ----------
def query_with_structured_output(nl_query: str, schema: str, max_retries: int = 2):
    """完整的 SQL Agent 流程，返回结构化结果

    Returns:
        dict: {
            "query": str,            # 原始问题
            "sql": str,              # 生成的 SQL
            "explanation": str,      # SQL 中文解释
            "columns": list,         # 返回的列名
            "data": list,            # 查询结果（行列表）
            "total_rows": int,
            "retries": int,
            "success": bool,
            "error": str | None,
        }
    """
    outcome = generate_sql_with_retry(nl_query, schema, max_retries)
    sql = outcome["sql"]

    if not outcome["success"]:
        return {
            "query": nl_query,
            "sql": sql,
            "explanation": "",
            "columns": [],
            "data": [],
            "total_rows": 0,
            "retries": outcome["retries"],
            "success": False,
            "error": outcome["final_error"],
        }

    result = outcome["result"]
    explanation = explain_sql(sql, nl_query)

    return {
        "query": nl_query,
        "sql": sql,
        "explanation": explanation,
        "columns": result["columns"],
        "data": result["data"],
        "total_rows": result["total_rows"],
        "retries": outcome["retries"],
        "success": True,
        "error": None,
    }


# ---------- 测评脚本 ----------
def run_evaluation():
    """运行SQL Agent测评，返回结果报告"""
    print("=" * 60)
    print("SQL Agent 测评")
    print("=" * 60)
    
    schema = get_schema()
    
    TEST_QUERIES = [
        "哪个产品卖得最多？",
        "北京的用户花了多少钱？",
        "各城市的订单总额排名",
        "哪个客户消费最高？",
        "哪个类别的产品销量最好？",
        "上海的用户有几个？",
        "所有订单总金额是多少？",
        "单价最高的产品是什么？",
        "2024年6月的订单有多少？",
        "销量最低的产品是什么？",
    ]
    
    total = len(TEST_QUERIES)
    success = 0
    avg_retries = 0
    
    results = []
    for i, q in enumerate(TEST_QUERIES):
        print(f"\n[{i+1}/{total}] {q}")
        res = query_with_structured_output(q, schema)
        results.append(res)
        
        if res["success"]:
            success += 1
            print(f"  ✅ 成功 (重试 {res['retries']}次)")
        else:
            print(f"  ❌ 失败: {res['error']}")
        avg_retries += res["retries"]
    
    success_rate = round(success / total * 100, 1)
    avg_retries = round(avg_retries / total, 2)
    
    # 生成报告
    report = f"""# SQL Agent 测评报告
| 指标 | 数值 |
|------|------|
| 测试用例数 | {total} |
| 成功率 | {success_rate}% |
| 平均重试次数 | {avg_retries} |

## 测试结果：
"""
    for i, res in enumerate(results):
        status = "✅" if res["success"] else "❌"
        report += f"\n### {i+1}. {res['query']} — {status} (重试 {res['retries']}次)\n"
        if res["success"]:
            report += f"```sql\n{res['sql']}\n```\n"
            report += f"**解释**: {res['explanation']}\n"
        else:
            report += f"**错误**: {res['error']}\n"
    
    with open("evaluation_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n{'='*60}")
    print(f"📊 测评结果: 成功率 {success_rate}%, 平均重试 {avg_retries}次")
    print(f"报告已保存到 evaluation_report.md")
    return success_rate, avg_retries


# ---------- 测试 ----------
if __name__ == "__main__":
    # 运行测评
    if len(sys.argv) > 1 and sys.argv[1] == "eval":
        run_evaluation()
        sys.exit(0)
    
    # 普通测试
    schema = get_schema()
    print("数据库结构:\n", schema)

    queries = [
        "哪个产品卖得最多？按销量排序",
        "北京的用户花了多少钱？",
        "各城市的订单总额排名",
    ]

    for q in queries:
        print(f"\n{'='*60}")
        print(f"用户: {q}")

        result = query_with_structured_output(q, schema)

        if result["success"]:
            print(f"SQL (重试{result['retries']}次):\n{result['sql']}")
            print(f"\n解释: {result['explanation']}")
            print(f"\n结果 ({result['total_rows']} 行):")
            for row in result["data"]:
                print(f"  {row}")
        else:
            print(f"❌ 失败 (重试{result['retries']}次): {result['error']}")
