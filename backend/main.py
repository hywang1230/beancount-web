from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path

from app.routers import transactions, reports, accounts, files
from app.core.config import settings

# 创建FastAPI应用
app = FastAPI(
    title="Beancount Web API",
    description="Beancount记账系统API",
    version="1.0.0"
)

# 添加CORS中间件
# 获取允许的源地址，支持环境变量配置
allowed_origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://192.168.32.152:5173"
]

# 如果是开发环境，也可以从环境变量中获取额外的允许源
extra_origins = os.environ.get("ALLOWED_ORIGINS", "").split(",")
for origin in extra_origins:
    if origin.strip():
        allowed_origins.append(origin.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保data目录存在
data_dir = Path("../data")
data_dir.mkdir(exist_ok=True)

# 注册路由
app.include_router(transactions.router, prefix="/api/transactions", tags=["交易"])
app.include_router(reports.router, prefix="/api/reports", tags=["报表"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["账户"])
app.include_router(files.router, prefix="/api/files", tags=["文件"])

@app.get("/")
async def root():
    return {"message": "Beancount Web API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "服务运行正常"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 