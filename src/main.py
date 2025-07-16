"""沙盒API应用程序入口点"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from utils.logging_config import setup_logging
from routers.sandbox_router import router as sandbox_router

# 设置日志
setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description="一个基于Docker的安全Python代码执行环境"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sandbox_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=16009,
        reload=True
    )