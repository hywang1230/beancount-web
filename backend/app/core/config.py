from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # 应用基础配置
    app_name: str = "Beancount Web"
    debug: bool = True
    
    # 数据目录配置
    data_dir: Path = Path("../data")
    default_beancount_file: str = "main.beancount"
    
    # API配置
    api_prefix: str = "/api"
    
    # 数据库配置（可选，用于缓存）
    database_url: str = "sqlite:///./cache.db"
    
    # Beancount配置
    default_currency: str = "CNY"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

# 创建全局设置实例
settings = Settings()

# 确保数据目录存在
settings.data_dir.mkdir(exist_ok=True)

# 如果不存在默认beancount文件，创建一个示例文件
default_file_path = settings.data_dir / settings.default_beancount_file
if not default_file_path.exists():
    sample_content = '''option "title" "个人记账"
option "operating_currency" "CNY"

1900-01-01 open Assets:Cash CNY
1900-01-01 open Assets:Bank:Checking CNY
1900-01-01 open Assets:Bank:Savings CNY
1900-01-01 open Income:Salary CNY
1900-01-01 open Expenses:Food CNY
1900-01-01 open Expenses:Transport CNY
1900-01-01 open Expenses:Housing CNY
1900-01-01 open Liabilities:CreditCard CNY
1900-01-01 open Equity:Opening-Balances CNY

; 示例交易
2024-01-01 * "期初余额"
  Assets:Bank:Checking     10000.00 CNY
  Equity:Opening-Balances

2024-01-02 * "超市购物"
  Expenses:Food    150.00 CNY
  Assets:Cash
'''
    with open(default_file_path, 'w', encoding='utf-8') as f:
        f.write(sample_content) 