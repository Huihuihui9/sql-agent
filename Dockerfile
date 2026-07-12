# sql-agent Docker 部署配置

# ====== 构建阶段 ======
FROM python:3.12-slim AS builder

WORKDIR /app

# 先装依赖（利用 Docker 缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# ====== 运行阶段 ======
FROM python:3.12-slim

WORKDIR /app

# 从构建阶段复制已安装的包
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app

# 如果存在 .env 文件，需要运行时挂载或构建时传入
# 这里不复制 .env，通过环境变量传入
ENV DEEPSEEK_API_KEY=""
ENV DEEPSEEK_API_BASE="https://api.deepseek.com/v1"
ENV DEEPSEEK_MODEL="deepseek-chat"

# 确保数据库存在
RUN python database.py

# Streamlit 默认端口
EXPOSE 8501

# 启动 Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
