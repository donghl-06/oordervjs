from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
# from fastapi.websockets import WebSocket
from ordervis_server.routers import auth, progress, tradebook
import uvicorn
import os
from ordervis_server.package import backend_logger
from ordervis_server.routers import websocket
import logging
from ordervis_server.utils.adata_session import ensure_adata_session

# 配置日志
logger = backend_logger.Log("ordervis")
log_level = backend_logger.LogLevel
log = logging.getLogger('uvicorn')
log.setLevel(logging.ERROR)

# 创建FastAPI应用
app = FastAPI(
    title="OrderVis Server",
    description="订单可视化服务器API",
    version="1.0.0"
)

# 添加Gzip压缩中间件
app.add_middleware(
    GZipMiddleware, 
    minimum_size=1000,  # 只压缩大于1KB的响应
    compresslevel=6     # 压缩级别(1-9)，6是平衡点
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 应用启动事件：登录 adata
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化操作"""
    try:
        if ensure_adata_session():
            logger.n_log("adata 会话已就绪（启动时校验/登录）", log_level.INFO)
        else:
            logger.n_log(
                "adata 启动时未能建立会话：请检查 aq_username / aq_password",
                log_level.WARNING,
            )
    except Exception as e:
        logger.n_log(f"adata 启动会话初始化异常: {e}", log_level.ERROR)
        # 不抛出异常，允许应用继续启动

# 注册路由
app.include_router(auth.router, prefix="/basic-api", tags=["认证"])
app.include_router(tradebook.router, prefix="/basic-api", tags=["TradeBook"])
app.include_router(progress.router, prefix="/basic-api", tags=["Progress"])  # HTTP progress API
app.include_router(websocket.router, tags=["WebSocket"])  # WebSocket 不使用 /basic-api 前缀

# 全局异常处理
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    ip = request.client.host
    path = request.url.path
    response_body = {
        "msg": "您期望请求的实体或资源不存在",
        "data": {},
        "length": 0
    }
    logger.n_log("{} > {} - 404".format(ip, path), log_level.INFO)
    return JSONResponse(status_code=404, content=response_body)

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: HTTPException):
    ip = request.client.host
    path = request.url.path
    response_body = {
        "msg": "服务器发生内部错误，请联系服务器管理员",
        "data": {},
        "length": 0
    }
    logger.n_log("{} > {} - 500({})".format(ip, path, str(exc)), log_level.ERROR)
    return JSONResponse(status_code=500, content=response_body)


if __name__ == "__main__":
    os.environ["GEVENT_SUPPORT"] = 'True'
    os.environ["PYDEVD_USE_FRAME_EVAL"] = "NO"
        
    uvicorn.run(
        "ordervis_server.main:app",
        host="0.0.0.0",
        port=18080,
        reload=True,
        log_level="info"
    ) 