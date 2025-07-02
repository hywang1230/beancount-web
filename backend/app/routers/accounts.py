from fastapi import APIRouter, HTTPException
from typing import List

from app.services.beancount_service import beancount_service

router = APIRouter()

@router.get("/", response_model=List[str])
async def get_all_accounts():
    """获取所有账户列表"""
    try:
        accounts = beancount_service.get_all_accounts()
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户列表失败: {str(e)}")

@router.get("/structure")
async def get_account_structure():
    """获取账户结构树"""
    try:
        accounts = beancount_service.get_all_accounts()
        
        # 构建账户树
        tree = {}
        
        for account in accounts:
            parts = account.split(':')
            current = tree
            
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        def build_tree_structure(node, prefix=""):
            result = []
            for key, value in node.items():
                full_path = f"{prefix}:{key}" if prefix else key
                item = {
                    "name": key,
                    "full_path": full_path,
                    "children": build_tree_structure(value, full_path) if value else []
                }
                result.append(item)
            return result
        
        structured_accounts = build_tree_structure(tree)
        
        return {
            "accounts": structured_accounts,
            "total_count": len(accounts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户结构失败: {str(e)}")

@router.get("/types")
async def get_accounts_by_type():
    """按类型分组获取账户"""
    try:
        accounts = beancount_service.get_all_accounts()
        
        grouped = {
            "Assets": [],
            "Liabilities": [],
            "Equity": [],
            "Income": [],
            "Expenses": [],
            "Other": []
        }
        
        for account in accounts:
            if account.startswith('Assets:'):
                grouped["Assets"].append(account)
            elif account.startswith('Liabilities:'):
                grouped["Liabilities"].append(account)
            elif account.startswith('Equity:'):
                grouped["Equity"].append(account)
            elif account.startswith('Income:'):
                grouped["Income"].append(account)
            elif account.startswith('Expenses:'):
                grouped["Expenses"].append(account)
            else:
                grouped["Other"].append(account)
        
        # 对每个分组进行排序
        for key in grouped:
            grouped[key].sort()
        
        return grouped
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户分组失败: {str(e)}")

@router.get("/suggest/{partial_name}")
async def suggest_accounts(partial_name: str):
    """根据部分名称建议账户"""
    try:
        accounts = beancount_service.get_all_accounts()
        
        # 模糊匹配
        suggestions = []
        partial_lower = partial_name.lower()
        
        for account in accounts:
            if partial_lower in account.lower():
                suggestions.append(account)
        
        # 优先完全匹配，然后按相似度排序
        exact_matches = [acc for acc in suggestions if acc.lower().startswith(partial_lower)]
        partial_matches = [acc for acc in suggestions if not acc.lower().startswith(partial_lower)]
        
        result = exact_matches + partial_matches
        
        return {
            "suggestions": result[:50],  # 最多返回50个建议
            "total_matches": len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户建议失败: {str(e)}") 