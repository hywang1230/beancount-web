#!/bin/bash

# 设置错误时退出
set -e

echo "开始启动 Beancount Web..."

# 确保数据目录存在
mkdir -p /app/data

# 检查数据库是否存在，如果不存在则初始化
if [ ! -f "/app/data/beancount-web.db" ]; then
    echo "数据库文件不存在，正在初始化..."
    python init_db.py
else
    echo "数据库文件已存在"
fi

# 运行数据库迁移（如果有新的迁移）
echo "检查数据库迁移..."
python -c "
import os
os.environ.setdefault('PYTHONPATH', '/app')
from alembic import command
from alembic.config import Config
try:
    cfg = Config('alembic.ini')
    command.upgrade(cfg, 'head')
    print('数据库迁移完成')
except Exception as e:
    print(f'数据库迁移警告: {e}')
    # 继续启动，即使迁移失败
"

# 启动应用
echo "启动FastAPI应用..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
