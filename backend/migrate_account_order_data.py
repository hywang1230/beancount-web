#!/usr/bin/env python3
"""
账户排序数据迁移脚本
将现有的JSON文件配置迁移到数据库中
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.account_order_service import account_order_service
from app.database import init_database
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """执行数据迁移"""
    logger.info("开始账户排序数据迁移...")
    
    try:
        # 确保数据库已初始化
        logger.info("初始化数据库...")
        init_database()
        
        # 检查JSON文件是否存在
        json_file = account_order_service.order_file
        if not json_file.exists():
            logger.info(f"未找到JSON配置文件: {json_file}")
            logger.info("将使用默认配置初始化数据库")
            
            # 初始化默认配置
            default_categories = ["Assets", "Liabilities", "Income", "Expenses", "Equity"]
            account_order_service.update_category_order(default_categories)
            logger.info("已初始化默认分类排序")
            
        else:
            logger.info(f"找到JSON配置文件: {json_file}")
            
            # 尝试从JSON迁移数据
            success = account_order_service.migrate_from_json()
            
            if success:
                logger.info("数据迁移成功完成！")
                
                # 验证迁移结果
                config = account_order_service.get_order_config()
                logger.info("迁移后的配置验证:")
                logger.info(f"- 分类排序: {config['category_order']}")
                logger.info(f"- 子分类数量: {sum(len(subs) for subs in config['subcategory_order'].values())}")
                logger.info(f"- 账户排序数量: {sum(sum(len(accounts) for accounts in cat.values()) for cat in config['account_order'].values())}")
                
                # 可选：备份JSON文件
                backup_file = json_file.with_suffix('.json.backup')
                if not backup_file.exists():
                    import shutil
                    shutil.copy2(json_file, backup_file)
                    logger.info(f"已备份原始JSON文件到: {backup_file}")
                
                logger.info("建议：迁移完成后可以删除原始JSON文件，系统将完全使用数据库存储配置")
                
            else:
                logger.error("数据迁移失败！")
                return 1
                
    except Exception as e:
        logger.error(f"迁移过程中发生错误: {e}")
        return 1
    
    logger.info("账户排序数据迁移完成")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
