from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
# 允许所有域名的跨域访问
allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保data目录存在（使用配置中的路径）
settings.data_dir.mkdir(exist_ok=True)

# 注册API路由
app.include_router(transactions.router, prefix="/api/transactions", tags=["交易"])
app.include_router(reports.router, prefix="/api/reports", tags=["报表"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["账户"])
app.include_router(files.router, prefix="/api/files", tags=["文件"])

@app.get("/api")
async def api_root():
    return {"message": "Beancount Web API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "服务运行正常"}

# 静态文件配置
static_dir = Path("static")

if static_dir.exists():
    # 定义可能的静态资源子目录
    static_subdirs = {
        "js": "js",
        "css": "css", 
        "img": "img",
        "fonts": "fonts",
        "media": "media"
    }
    
    # 只挂载存在的子目录
    for mount_path, dir_name in static_subdirs.items():
        subdir_path = static_dir / dir_name
        if subdir_path.exists() and subdir_path.is_dir():
            app.mount(f"/{mount_path}", StaticFiles(directory=str(subdir_path)), name=mount_path)
    
    # 处理favicon和其他根级文件
    @app.get("/favicon.ico")
    async def favicon():
        # 首先尝试查找favicon.ico
        favicon_path = static_dir / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        
        # 然后尝试favicon.svg
        favicon_svg_path = static_dir / "favicon.svg"
        if favicon_svg_path.exists():
            return FileResponse(favicon_svg_path)
        
        # 如果都不存在，返回404
        raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/")
async def root():
    """根路径处理"""
    if static_dir.exists():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    return {"message": "Beancount Web API", "version": "1.0.0"}

if static_dir.exists():
    # 处理SPA路由回退 - 必须在所有其他路由之后
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        处理SPA路由回退，对于所有非API路由返回index.html
        """
        # 如果是API路由，让FastAPI处理
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # 检查是否为静态文件
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # 对于所有其他路由，返回index.html让前端路由器处理
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        else:
            raise HTTPException(status_code=404, detail="Application not found")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 