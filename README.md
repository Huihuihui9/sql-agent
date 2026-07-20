# SQL 数据分析 Agent

自然语言查询数据库 — 你说人话，AI 帮你写 SQL。

## ✨ 功能特性

- 自然语言输入 → 自动生成 SQL
- **智能自动重试**：SQL执行错误时自动让LLM修正，最多重试2次
- **结构化输出**：统一返回结构化结果，包含SQL、解释、数据三部分
- 安全执行（只读、白名单表、危险查询拦截）
- 结果表格展示
- SQL 中文解释（面向非技术人员）
- 示例问题一键体验
- **内置测评体系**：10条测试用例自动跑，输出成功率 + 平均重试次数

## 安全设计

三层防护机制：
1. **只读连接**：只允许 SELECT 查询，禁止 DROP/DELETE/UPDATE/INSERT
2. **白名单表**：明确指定可查询的表（users/products/orders）
3. **行数限制**：最多返回 30 行，防止内存溢出
4. **关键字边界校验**：通过单词边界匹配防止误杀

## 技术栈

- LLM：DeepSeek
- 数据库：SQLite
- 界面：Streamlit
- 安全：SQL 静态分析 + 只读执行
- 其他：Pydantic 结构化输出

## 快速开始

### 前置依赖
```bash
pip install -r requirements.txt
```

### 第一步：创建示例数据库
```bash
python database.py
```

### 第二步：启动界面
```bash
streamlit run app.py
```

浏览器自动打开 http://localhost:8501

## 使用方式

### 基础查询
1. 输入自然语言问题，如 "哪个产品卖得最多？"
2. 系统自动生成SQL → 安全执行 → 展示结果
3. 如果执行失败，系统自动重试最多2次

### 一键测评
点击侧边栏的 "📊 运行SQL Agent测评"，系统自动跑完10条测试用例，生成报告显示：
- 整体成功率 (0-100%)
- 平均重试次数
- 每条测试用例的详细执行结果

也可以通过命令行测评：
```bash
python sql_agent.py eval
# 生成 evaluation_report.md 完整报告
```

## 示例问题

- 哪个产品卖得最多？
- 北京的用户花了多少钱？
- 各城市的订单总额排名
- 哪个客户消费最高？
- 哪个类别的产品销量最好？

## 项目结构

```
sql-agent/
├── app.py                  # Streamlit 主界面（含测评入口）
├── database.py             # 数据库定义 + 初始化
├── sql_agent.py            # SQL生成 + 安全执行 + 自动重试 + 结构化输出（v2.0）
├── agent_demo.py           # Tool Calling Agent 演示（计算器+SQL）
├── 06_web_search_agent.py  # 联网搜索 Agent（Wikipedia）
├── 07_mcp_server.py       # MCP 协议服务器
├── llm_config.py          # LLM配置统一管理
├── Dockerfile              # 容器化部署
├── docker-compose.yml      # 多服务编排
├── nginx.conf             # Nginx 反向代理
├── demo_script.md         # 4分钟演示脚本
├── requirements.txt        # 完整依赖
└── README.md
```

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | - | 初始版本 |
| v2.0 | 2026-07-20 | 新增 自动SQL重试 + 结构化输出 + 内置测评体系 |
