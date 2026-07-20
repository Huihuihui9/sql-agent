import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from database import get_schema
from sql_agent import generate_sql_with_retry, explain_sql, execute_safe_query, query_with_structured_output

st.set_page_config(page_title="SQL 数据分析 Agent", page_icon="📊", layout="wide")

st.title("📊 SQL 数据分析 Agent")
st.caption("输入自然语言，自动生成SQL并查询数据库")

def main():
    schema = get_schema()

    # 侧边栏：显示数据库结构
    with st.sidebar:
        st.header("📁 数据库结构")
        st.code(schema, language="text")

        st.divider()
        st.markdown("**示例问题：**")
        examples = [
            "哪个产品卖得最多？",
            "北京的用户花了多少钱？",
            "各城市的订单总额排名",
            "哪个客户消费最高？",
            "哪个类别的产品销量最好？",
        ]
        for ex in examples:
            if st.button(ex, use_container_width=True, type="secondary"):
                st.session_state["example_query"] = ex

        # 新增测评入口
        st.divider()
        if st.button("📊 运行SQL Agent测评", use_container_width=True):
            st.session_state["run_eval"] = True

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "run_eval" not in st.session_state:
        st.session_state["run_eval"] = False

    # 测评模式
    if st.session_state["run_eval"]:
        st.subheader("📊 SQL Agent 测评结果")
        with st.spinner("正在运行10条测试用例..."):
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
                res = query_with_structured_output(q, schema)
                results.append(res)
                if res["success"]:
                    success += 1
                avg_retries += res["retries"]
                st.progress((i+1)/total, text=f"测试用例 {i+1}/{total}")

            avg_retries = round(avg_retries/total, 2)
            success_rate = round(success/total * 100, 1)

            # 展示结果
            st.metric("✅ 成功率", f"{success_rate}%")
            st.metric("🔄 平均重试次数", f"{avg_retries}")

            st.subheader("逐条测试结果")
            for i, res in enumerate(results):
                status = "✅ 成功" if res["success"] else "❌ 失败"
                with st.expander(f"用例 {i+1}: {res['query']} — {status} (重试 {res['retries']}次)"):
                    if res["success"]:
                        st.code(res["sql"], language="sql")
                        st.caption(res["explanation"])
                        st.dataframe(res["data"])
                    else:
                        st.error(res["error"])

            st.session_state["run_eval"] = False
            return

    # 显示对话历史
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sql"):
                with st.expander("📝 生成的SQL"):
                    st.code(msg["sql"], language="sql")
            if msg.get("data"):
                st.dataframe(msg["data"])
            if msg.get("explain"):
                st.caption(f"💡 {msg['explain']}")

    # 获取用户输入
    query = st.chat_input("输入你想查询的内容...")

    if not query:
        query = st.session_state.get("example_query", "")
        if query:
            st.session_state["example_query"] = ""

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            with st.status("🤔 正在思考...") as status:
                # Step 1: 生成并执行SQL（带自动重试+结构化输出）
                status.update(label="生成SQL并执行", state="running")
                result = query_with_structured_output(query, schema)

                if result["success"]:
                    status.update(label=f"✅ 查询完成 ({result['total_rows']} 行, 重试 {result['retries']}次)", state="complete")
                    st.code(result["sql"], language="sql")
                    st.dataframe(result["data"])
                    st.caption(f"💡 {result['explanation']}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"查询完成，返回 {result['total_rows']} 行结果",
                        "sql": result["sql"],
                        "data": result["data"],
                        "explain": result["explanation"],
                    })
                else:
                    status.update(label="❌ 查询失败", state="error")
                    st.error(f"执行失败: {result['error']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ 发生错误: {str(e)}")
        if os.getenv("ENV") == "development":
            st.exception(e)
