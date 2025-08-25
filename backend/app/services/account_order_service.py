import json
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.core.config import settings
from app.database import get_db
from app.models.account_order import AccountOrder


class AccountOrderService:
    def __init__(self):
        self.data_dir = settings.data_dir
        self.order_file = self.data_dir / "account_order.json"
        
    def _get_db_session(self) -> Session:
        """获取数据库会话"""
        return next(get_db())
        
    def _load_order_config(self) -> Dict:
        """从数据库加载账户排序配置"""
        db = self._get_db_session()
        try:
            # 获取分类排序
            category_orders = db.query(AccountOrder).filter(
                AccountOrder.order_type == 'category'
            ).order_by(AccountOrder.sort_order).all()
            
            category_order = [order.item_name for order in category_orders]
            if not category_order:
                category_order = ["Assets", "Liabilities", "Income", "Expenses", "Equity"]
            
            # 获取子分类排序
            subcategory_order = {}
            subcategory_orders = db.query(AccountOrder).filter(
                AccountOrder.order_type == 'subcategory'
            ).order_by(AccountOrder.category, AccountOrder.sort_order).all()
            
            for order in subcategory_orders:
                if order.category not in subcategory_order:
                    subcategory_order[order.category] = []
                subcategory_order[order.category].append(order.item_name)
            
            # 确保所有分类都有子分类配置
            for category in category_order:
                if category not in subcategory_order:
                    subcategory_order[category] = []
            
            # 获取账户排序
            account_order = {}
            account_orders = db.query(AccountOrder).filter(
                AccountOrder.order_type == 'account'
            ).order_by(AccountOrder.category, AccountOrder.subcategory, AccountOrder.sort_order).all()
            
            for order in account_orders:
                if order.category not in account_order:
                    account_order[order.category] = {}
                if order.subcategory not in account_order[order.category]:
                    account_order[order.category][order.subcategory] = []
                account_order[order.category][order.subcategory].append(order.item_name)
            
            # 确保所有分类都有账户配置
            for category in category_order:
                if category not in account_order:
                    account_order[category] = {}
            
            return {
                "category_order": category_order,
                "subcategory_order": subcategory_order,
                "account_order": account_order
            }
        except Exception as e:
            # 使用默认配置，静默处理错误
            return {
                "category_order": ["Assets", "Liabilities", "Income", "Expenses", "Equity"],
                "subcategory_order": {
                    "Assets": [],
                    "Liabilities": [],
                    "Income": [],
                    "Expenses": [],
                    "Equity": []
                },
                "account_order": {
                    "Assets": {},
                    "Liabilities": {},
                    "Income": {},
                    "Expenses": {},
                    "Equity": {}
                }
            }
        finally:
            db.close()
    
    def _save_category_order(self, category_order: List[str]):
        """保存分类排序到数据库"""
        db = self._get_db_session()
        try:
            # 删除现有的分类排序记录
            db.query(AccountOrder).filter(AccountOrder.order_type == 'category').delete()
            
            # 创建新的分类排序记录
            for idx, category in enumerate(category_order):
                order_record = AccountOrder(
                    order_type='category',
                    category=None,
                    subcategory=None,
                    item_name=category,
                    sort_order=idx
                )
                db.add(order_record)
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"保存分类排序配置失败: {e}")
        finally:
            db.close()
    
    def _save_subcategory_order(self, category: str, subcategory_order: List[str]):
        """保存子分类排序到数据库"""
        db = self._get_db_session()
        try:
            # 删除指定分类的子分类排序记录
            db.query(AccountOrder).filter(
                and_(
                    AccountOrder.order_type == 'subcategory',
                    AccountOrder.category == category
                )
            ).delete()
            
            # 创建新的子分类排序记录
            for idx, subcategory in enumerate(subcategory_order):
                order_record = AccountOrder(
                    order_type='subcategory',
                    category=category,
                    subcategory=None,
                    item_name=subcategory,
                    sort_order=idx
                )
                db.add(order_record)
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"保存子分类排序配置失败: {e}")
        finally:
            db.close()
    
    def _save_account_order(self, category: str, subcategory: str, account_order: List[str]):
        """保存账户排序到数据库"""
        db = self._get_db_session()
        try:
            # 删除指定分类和子分类的账户排序记录
            db.query(AccountOrder).filter(
                and_(
                    AccountOrder.order_type == 'account',
                    AccountOrder.category == category,
                    AccountOrder.subcategory == subcategory
                )
            ).delete()
            
            # 创建新的账户排序记录
            for idx, account in enumerate(account_order):
                order_record = AccountOrder(
                    order_type='account',
                    category=category,
                    subcategory=subcategory,
                    item_name=account,
                    sort_order=idx
                )
                db.add(order_record)
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"保存账户排序配置失败: {e}")
        finally:
            db.close()
    
    def get_order_config(self) -> Dict:
        """获取账户排序配置"""
        return self._load_order_config()
    
    def update_category_order(self, category_order: List[str]) -> Dict:
        """更新账户分类排序"""
        self._save_category_order(category_order)
        return self._load_order_config()
    
    def update_subcategory_order(self, category: str, subcategory_order: List[str]) -> Dict:
        """更新子分类排序"""
        self._save_subcategory_order(category, subcategory_order)
        return self._load_order_config()
    
    def update_account_order(self, category: str, subcategory: str, account_order: List[str]) -> Dict:
        """更新指定子分类的账户排序"""
        self._save_account_order(category, subcategory, account_order)
        return self._load_order_config()
    
    def sort_accounts(self, accounts: List[str]) -> List[str]:
        """根据配置对账户列表进行排序"""
        config = self._load_order_config()
        
        # 按分类分组
        categorized_accounts = {}
        for account in accounts:
            if ':' in account:
                category = account.split(':')[0]
                if category not in categorized_accounts:
                    categorized_accounts[category] = []
                categorized_accounts[category].append(account)
            else:
                # 处理顶级账户
                if 'top_level' not in categorized_accounts:
                    categorized_accounts['top_level'] = []
                categorized_accounts['top_level'].append(account)
        
        sorted_accounts = []
        
        # 按配置的分类顺序排序
        category_order = config.get("category_order", ["Assets", "Liabilities", "Equity", "Income", "Expenses"])
        
        for category in category_order:
            if category in categorized_accounts:
                category_accounts = categorized_accounts[category]
                sorted_category_accounts = self._sort_accounts_in_category(category, category_accounts, config)
                sorted_accounts.extend(sorted_category_accounts)
        
        # 添加其他未配置的分类
        for category, category_accounts in categorized_accounts.items():
            if category not in category_order and category != 'top_level':
                sorted_category_accounts = self._sort_accounts_in_category(category, category_accounts, config)
                sorted_accounts.extend(sorted_category_accounts)
        
        # 添加顶级账户
        if 'top_level' in categorized_accounts:
            sorted_accounts.extend(sorted(categorized_accounts['top_level']))
        
        return sorted_accounts
    
    def _sort_accounts_in_category(self, category: str, accounts: List[str], config: Dict) -> List[str]:
        """对分类内的账户进行排序"""
        subcategory_order = config.get("subcategory_order", {}).get(category, [])
        account_order_config = config.get("account_order", {}).get(category, {})
        
        # 按子分类分组
        subcategorized_accounts = {}
        for account in accounts:
            parts = account.split(':')
            if len(parts) >= 2:
                subcategory = parts[1]
                if subcategory not in subcategorized_accounts:
                    subcategorized_accounts[subcategory] = []
                subcategorized_accounts[subcategory].append(account)
        
        sorted_accounts = []
        
        # 按配置的子分类顺序排序
        for subcategory in subcategory_order:
            if subcategory in subcategorized_accounts:
                subcategory_accounts = subcategorized_accounts[subcategory]
                
                # 如果有具体的账户排序配置，使用配置的顺序
                if subcategory in account_order_config:
                    ordered_accounts = account_order_config[subcategory]
                    # 先添加配置中的账户（按配置顺序）
                    for account in ordered_accounts:
                        if account in subcategory_accounts:
                            sorted_accounts.append(account)
                    # 再添加未配置的账户（按字母顺序）
                    remaining_accounts = [acc for acc in subcategory_accounts if acc not in ordered_accounts]
                    sorted_accounts.extend(sorted(remaining_accounts))
                else:
                    # 没有具体配置，按字母顺序排序
                    sorted_accounts.extend(sorted(subcategory_accounts))
        
        # 添加其他未配置的子分类
        for subcategory, subcategory_accounts in subcategorized_accounts.items():
            if subcategory not in subcategory_order:
                if subcategory in account_order_config:
                    ordered_accounts = account_order_config[subcategory]
                    for account in ordered_accounts:
                        if account in subcategory_accounts:
                            sorted_accounts.append(account)
                    remaining_accounts = [acc for acc in subcategory_accounts if acc not in ordered_accounts]
                    sorted_accounts.extend(sorted(remaining_accounts))
                else:
                    sorted_accounts.extend(sorted(subcategory_accounts))
        
        return sorted_accounts
    
    def get_subcategories(self, category: str, accounts: List[str]) -> List[str]:
        """获取指定分类下的所有子分类"""
        subcategories = set()
        for account in accounts:
            if account.startswith(f"{category}:"):
                parts = account.split(':')
                if len(parts) >= 2:
                    subcategories.add(parts[1])
        
        subcategory_list = sorted(list(subcategories))
        
        # 应用排序配置
        config = self._load_order_config()
        subcategory_order = config.get("subcategory_order", {}).get(category, [])
        
        if subcategory_order:
            # 按配置的顺序排列
            ordered = []
            for sub in subcategory_order:
                if sub in subcategory_list:
                    ordered.append(sub)
            # 添加未配置的子分类（按字母顺序）
            for sub in subcategory_list:
                if sub not in ordered:
                    ordered.append(sub)
            return ordered
        else:
            return subcategory_list
    
    def get_accounts_by_category(self, category: str, accounts: List[str]) -> List[str]:
        """获取指定分类下的所有账户"""
        category_accounts = [acc for acc in accounts if acc.startswith(f"{category}:")]
        return self._sort_accounts_in_category(category, category_accounts, self._load_order_config())
    
    def get_accounts_in_subcategory(self, category: str, subcategory: str, accounts: List[str]) -> List[str]:
        """获取指定子分类下的所有账户"""
        subcategory_accounts = [
            acc for acc in accounts 
            if acc.startswith(f"{category}:{subcategory}:")
        ]
        
        config = self._load_order_config()
        account_order_config = config.get("account_order", {}).get(category, {}).get(subcategory, [])
        
        if account_order_config:
            sorted_accounts = []
            # 先添加配置中的账户（按配置顺序）
            for account in account_order_config:
                if account in subcategory_accounts:
                    sorted_accounts.append(account)
            # 再添加未配置的账户（按字母顺序）
            remaining_accounts = [acc for acc in subcategory_accounts if acc not in account_order_config]
            sorted_accounts.extend(sorted(remaining_accounts))
            return sorted_accounts
        else:
            return sorted(subcategory_accounts)

    def migrate_from_json(self) -> bool:
        """从JSON文件迁移数据到数据库"""
        if not self.order_file.exists():
            return False
            
        try:
            with open(self.order_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 迁移分类排序
            category_order = config.get("category_order", [])
            if category_order:
                self._save_category_order(category_order)
            
            # 迁移子分类排序
            subcategory_order = config.get("subcategory_order", {})
            for category, subcategories in subcategory_order.items():
                if subcategories:
                    self._save_subcategory_order(category, subcategories)
            
            # 迁移账户排序
            account_order = config.get("account_order", {})
            for category, category_accounts in account_order.items():
                for subcategory, accounts in category_accounts.items():
                    if accounts:
                        self._save_account_order(category, subcategory, accounts)
            
            return True
        except Exception as e:
            print(f"迁移JSON配置失败: {e}")
            return False


# 创建全局实例
account_order_service = AccountOrderService()