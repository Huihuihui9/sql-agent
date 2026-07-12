"""
补4: 联网搜索 Agent — 用 Wikipedia 做知识检索
概念：和 SQL Agent 同一个模式，只是工具换成「搜索网页」
流程：LLM决定需要搜 → 调用 Wikipedia API → 拿结果回LLM → 生成回答

注意：真实的 web search 需要 SerpAPI/Tavily 等付费服务，
这里用 Wikipedia API 做搜索演示（免费、无需API Key、概念一致）
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

llm = ChatOpenAI(api_key=api_key, base_url=base_url, model=model, temperature=0.3)


# ====== 定义工具 ======

@tool
def calculator(expression: str) -> str:
    """计算数学表达式，如 '25 * 4 + 100' 或 '15800 * 0.85'"""
    try:
        allowed = {"abs": abs, "max": max, "min": min, "round": round}
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


@tool
def query_sales_db(question: str) -> list:
    """用自然语言查询销售数据库，如'哪个产品卖得最多'"""
    # 切换到 sql-agent 目录确保找到 database
    old_dir = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        import importlib
        sql_agent = importlib.import_module("sql_agent")
        schema = sql_agent.get_schema()
        sql = sql_agent.generate_sql(question, schema)
        result = sql_agent.execute_safe_query(sql)
        if result["success"]:
            return result["data"]
        return [{"error": result["error"]}]
    finally:
        os.chdir(old_dir)


@tool
def web_search(query: str) -> str:
    """搜索网络获取最新信息。适用于需要实时/外部知识的问题。
    用 Wikipedia 作为搜索源（免费、无需API Key、自动识别中英文）。"""
    import requests, re

    headers = {"User-Agent": "WebSearchAgent/1.0 (learning demo)"}

    try:
        def _search_wikipedia(domain, query, limit=3):
            """在指定 Wikipedia 域名搜索"""
            url = f"https://{domain}/w/api.php"
            params = {"action": "query", "list": "search",
                      "srsearch": query, "format": "json", "srlimit": limit}
            r = requests.get(url, params=params, headers=headers, timeout=10)
            return r.json().get("query", {}).get("search", [])

        def _get_extract(domain, title):
            """获取 Wikipedia 文章摘要"""
            params = {"action": "query", "titles": title,
                      "prop": "extracts", "exintro": True,
                      "explaintext": True, "format": "json", "redirects": 1}
            r = requests.get(f"https://{domain}/w/api.php",
                             params=params, headers=headers, timeout=10)
            pages = r.json().get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                if pid != "-1" and "extract" in pdata:
                    return pdata["extract"][:600]
            return ""

        # 判断语言：如果查询含中文，优先搜中文 Wikipedia
        has_chinese = bool(re.search(r'[一-鿿]', query))
        domains = ["zh.wikipedia.org", "en.wikipedia.org"] if has_chinese else ["en.wikipedia.org"]

        all_results = []
        for domain in domains:
            results = _search_wikipedia(domain, query)
            if results:
                output_parts = []
                for i, item in enumerate(results[:3], 1):
                    snippet = re.sub(r'<[^>]+>', '', item["snippet"])
                    output_parts.append(f"[{i}] {item['title']}\n    {snippet}")

                # 第一个结果的详情
                extract = _get_extract(domain, results[0]["title"])
                if extract:
                    output_parts.append(f"\n详情 ({results[0]['title']}):\n{extract}")

                all_results.append(f"--- Wikipedia ({domain}) ---\n" + "\n\n".join(output_parts))
                if not has_chinese:
                    break  # 英文只需要搜一次

        if all_results:
            return "\n\n".join(all_results)
        return f"未找到 '{query}' 的相关结果"

    except requests.exceptions.Timeout:
        return f"搜索 '{query}' 超时"
    except Exception as e:
        return f"搜索出错: {e}"


tools = [calculator, query_sales_db, web_search]
llm_with_tools = llm.bind_tools(tools)


# ====== Agent 循环 ======
def run_agent(user_query: str, max_steps: int = 5):
    """手动实现Agent循环（ReAct模式）"""
    print(f"用户: {user_query}\n")
    messages = [HumanMessage(content=user_query)]

    for step in range(max_steps):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                print(f"  [{step+1}] 调用工具: {tool_name}({tool_args})")

                # 找到对应的工具函数
                for t in tools:
                    if t.name == tool_name:
                        result = t.invoke(tool_args)
                        break
                else:
                    result = f"未找到工具: {tool_name}"

                result_str = str(result)
                print(f"  [{step+1}] 工具返回: {result_str[:120]}...")
                messages.append(ToolMessage(content=result_str, tool_call_id=tc["id"]))
        else:
            break

    print(f"\n最终回答: {response.content}")
    return response.content


if __name__ == "__main__":
    print("=" * 60)
    print("Agent 演示：联网搜索 + 计算器 + SQL 查询")
    print("=" * 60)

    # 测试1: 计算器
    print("\n>>> 测试1: 计算")
    run_agent("计算 15800 * 0.85 等于多少？")
    print("\n" + "=" * 60)

    # 测试2: SQL查询
    print("\n>>> 测试2: 查数据库")
    run_agent("哪个产品卖得最多？")
    print("\n" + "=" * 60)

    # 测试3: 联网搜索（Wikipedia）
    print("\n>>> 测试3: 搜索")
    run_agent("用 Wikipedia 查一下 Python 编程语言的创始人和发布时间")
