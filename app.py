import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from database import get_schema
from sql_agent import generate_sql, execute_safe_query, explain_sql

st.set_page_config(page_title="SQL 数据分析Agent", page_icon="📊", layout="wide")

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

    if "messages" not in st.session_state:
        st.session_state.messages = []

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
                # Step 1: 生成SQL
                status.update(label="生成SQL", state="running")
                sql = generate_sql(query, schema)

                # Step 2: 执行SQL
                status.update(label="执行查询", state="running")
                result = execute_safe_query(sql)

                if result["success"]:
                    status.update(label=f"✅ 查询完成 ({result['showed_rows']} 行)", state="complete")
                    st.code(sql, language="sql")
                    st.dataframe(result["data"])

                    # Step 3: 解释SQL
                    exp = explain_sql(sql)
                    st.caption(f"💡 {exp}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"查询完成，返回 {result['showed_rows']} 行结果",
                        "sql": sql,
                        "data": result["data"],
                        "explain": exp,
                    })
                else:
                    status.update(label="❌ 查询失败", state="error")
                    st.error(f"执行失败: {result['error']}")


if __name__ == "__main__":
    main()
