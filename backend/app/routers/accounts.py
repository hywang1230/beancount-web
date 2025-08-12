from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict

from app.services.beancount_service import beancount_service
from app.services.account_order_service import account_order_service
from app.models.schemas import AccountCreate, AccountClose, AccountRestore, AccountActionResponse

router = APIRouter()

@router.get("/", response_model=List[str])
async def get_all_accounts():
    """获取活跃账户列表（排除已归档账户）"""
    try:
        accounts = beancount_service.get_active_accounts()
        # 应用排序
        sorted_accounts = account_order_service.sort_accounts(accounts)
        return sorted_accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户列表失败: {str(e)}")

@router.get("/archived", response_model=List[str])
async def get_archived_accounts():
    """获取已归档账户列表"""
    try:
        accounts = beancount_service.get_archived_accounts()
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取已归档账户列表失败: {str(e)}")

@router.get("/structure")
async def get_account_structure():
    """获取活跃账户结构树（排除已归档账户）"""
    try:
        accounts = beancount_service.get_active_accounts()
        
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
    """按类型分组获取活跃账户（排除已归档账户）"""
    try:
        accounts = beancount_service.get_active_accounts()
        
        grouped = {
            "Assets": [],
            "Liabilities": [],
            "Equity": [],
            "Income": [],
            "Expenses": []
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
        
        # 对每个分组应用排序
        for key in grouped:
            grouped[key] = account_order_service.sort_accounts(grouped[key])
        
        return grouped
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户分组失败: {str(e)}")

@router.get("/suggest/{partial_name}")
async def suggest_accounts(partial_name: str):
    """根据部分名称建议活跃账户（排除已归档账户）"""
    try:
        accounts = beancount_service.get_active_accounts()
        
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

@router.post("/create", response_model=AccountActionResponse)
async def create_account(account_data: AccountCreate):
    """创建新账户"""
    try:
        beancount_service.create_account(
            account_name=account_data.name,
            open_date=account_data.open_date,
            currencies=account_data.currencies,
            booking_method=account_data.booking_method
        )
        
        return AccountActionResponse(
            success=True,
            message="账户创建成功",
            account_name=account_data.name
        )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建账户失败: {str(e)}")

@router.post("/close", response_model=AccountActionResponse)
async def close_account(account_data: AccountClose):
    """归档账户"""
    try:
        success = beancount_service.close_account(
            account_name=account_data.name,
            close_date=account_data.close_date
        )
        
        if success:
            return AccountActionResponse(
                success=True,
                message="账户归档成功",
                account_name=account_data.name
            )
        else:
            raise HTTPException(status_code=400, detail="账户归档失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"归档账户失败: {str(e)}")

@router.post("/restore", response_model=AccountActionResponse)
async def restore_account(account_data: AccountRestore):
    """恢复账户（删除close指令）"""
    try:
        beancount_service.restore_account(account_data.name)
        
        return AccountActionResponse(
            success=True,
            message="账户恢复成功",
            account_name=account_data.name
        )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复账户失败: {str(e)}")

# 账户排序相关API
@router.get("/order/config")
async def get_account_order_config():
    """获取账户排序配置"""
    try:
        config = account_order_service.get_order_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排序配置失败: {str(e)}")

@router.put("/order/categories")
async def update_category_order(category_order: List[str] = Body(...)):
    """更新账户分类排序"""
    try:
        config = account_order_service.update_category_order(category_order)
        return {"success": True, "message": "分类排序更新成功", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新分类排序失败: {str(e)}")

@router.put("/order/subcategories/{category}")
async def update_subcategory_order(category: str, subcategory_order: List[str] = Body(...)):
    """更新子分类排序"""
    try:
        config = account_order_service.update_subcategory_order(category, subcategory_order)
        return {"success": True, "message": "子分类排序更新成功", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新子分类排序失败: {str(e)}")

@router.put("/order/accounts/{category}/{subcategory}")
async def update_account_order_in_subcategory(category: str, subcategory: str, account_order: List[str] = Body(...)):
    """更新指定子分类的账户排序"""
    try:
        config = account_order_service.update_account_order(category, subcategory, account_order)
        return {"success": True, "message": "账户排序更新成功", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新账户排序失败: {str(e)}")

@router.get("/order/subcategories/{category}")
async def get_subcategories(category: str):
    """获取指定分类下的所有子分类"""
    try:
        accounts = beancount_service.get_active_accounts()
        subcategories = account_order_service.get_subcategories(category, accounts)
        return {"subcategories": subcategories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取子分类失败: {str(e)}")

@router.get("/order/accounts/{category}/{subcategory}")
async def get_accounts_in_subcategory(category: str, subcategory: str):
    """获取指定子分类下的所有账户"""
    try:
        accounts = beancount_service.get_active_accounts()
        subcategory_accounts = account_order_service.get_accounts_in_subcategory(category, subcategory, accounts)
        return {"accounts": subcategory_accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取子分类账户失败: {str(e)}")