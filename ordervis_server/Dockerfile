FROM python:3.11
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gnupg2 \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | \
            gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
            https://packages.microsoft.com/debian/12/prod bookworm main" \
            > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18


# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install adata==0.2.5 -i https://pypi.aitopia.tech/simple/ --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple  
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.aitopia.tech/simple/ --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple 


# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/log /app/config

# 暴露端口
EXPOSE 18080

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "18080", "--workers", "1"] 