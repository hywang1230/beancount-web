#!/usr/bin/env python3
"""
数据库初始化脚本
用于在Docker容器启动时初始化SQLite数据库
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.database import init_database

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        logger.info("开始初始化数据库...")
        
        # 确保数据目录存在
        data_dir = settings.data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"数据目录: {data_dir}")
        
        # 初始化数据库
        init_database()
        
        logger.info("数据库初始化完成!")
        
        # 检查数据库文件是否存在
        db_file = data_dir / "beancount-web.db"
        if db_file.exists():
            logger.info(f"数据库文件已创建: {db_file}")
            logger.info(f"数据库文件大小: {db_file.stat().st_size} bytes")
        else:
            logger.warning("数据库文件未找到")
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
