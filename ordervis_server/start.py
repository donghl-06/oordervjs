import os
from multiprocessing import Process

if __name__ == "__main__":
    # 启动 FastAPI 服务器
    os.system("uvicorn main:app --host 0.0.0.0 --port 18080 --workers 4") 