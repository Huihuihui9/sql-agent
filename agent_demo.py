"""
Agent + Tool Calling 核心演示（手动实现）
原理：LLM决定要调用什么工具 → 自动执行工具 → 把结果给LLM → 生成回答
vs Chain：Chain是固定流程A→B→C，Agent是LLM自己决定下一步做什么
"""
import sys, os, json
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
    """计算数学表达式，如 '25 * 4 + 100'"""
    try:
        # 安全地计算表达式
        allowed = {"abs": abs, "max": max, "min": min, "round": round}
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


@tool
def query_sales_db(question: str) -> list:
    """用自然语言查询销售数据库，如'哪个产品卖得最多'"""
    from sql_agent import generate_sql, execute_safe_query, get_schema
    schema = get_schema()
    sql = generate_sql(question, schema)
    result = execute_safe_query(sql)
    if result["success"]:
        return result["data"]
    return [{"error": result["error"]}]


tools = [calculator, query_sales_db]
llm_with_tools = llm.bind_tools(tools)

# ====== Agent 循环 ======
def run_agent(user_query: str, max_steps: int = 5):
    """手动实现Agent循环"""
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

                print(f"  [{step+1}] 工具返回: {str(result)[:100]}...")
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        else:
            # 没有工具调用，表示LLM已经给出最终回答
            break

    print(f"\n最终回答: {response.content}")
    return response.content


if __name__ == "__main__":
    print("="*50)
    print("Agent 演示：自动选择工具")
    print("="*50)

    # Test 1: 计算器
    run_agent("计算 15800 * 0.85，然后把结果告诉我")
    print("\n" + "="*50 + "\n")

    # Test 2: SQL查询
    run_agent("查询哪个产品卖得最多，并告诉我销量")
    print("\n" + "="*50 + "\n")
