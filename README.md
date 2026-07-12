# SQL 数据分析 Agent

自然语言查询数据库 — 你说人话，AI 帮你写 SQL。

## 功能

- 自然语言输入 → 自动生成 SQL
- 安全执行（只读、白名单表、危险查询拦截）
- 结果表格展示
- SQL 中文解释（面向非技术人员）
- 示例问题一键体验

## 安全设计

- **只读连接**：只允许 SELECT 查询，禁止 DROP/DELETE/UPDATE/INSERT
- **白名单表**：明确指定可查询的表
- **行数限制**：最多返回 30 行

## 快速开始

```bash
pip install -r requirements.txt

# 第一步：创建示例数据库
python database.py

# 第二步：启动界面
streamlit run app.py
```

## 技术栈

- LLM：DeepSeek
- 数据库：SQLite
- 界面：Streamlit
- 安全：SQL 静态分析 + 只读执行

## 示例问题

- 哪个产品卖得最多？
- 北京的用户花了多少钱？
- 各城市的订单总额排名
- 哪个客户消费最高？
