from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date

from app.models.schemas import TransactionResponse, TransactionCreate, TransactionFilter
from app.services.beancount_service import beancount_service

router = APIRouter()

@router.get("/")
async def get_transactions(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    account: Optional[str] = Query(None, description="账户筛选"),
    payee: Optional[str] = Query(None, description="收付方筛选"),
    narration: Optional[str] = Query(None, description="摘要筛选"),
    amount_min: Optional[float] = Query(None, description="最小金额筛选"),
    amount_max: Optional[float] = Query(None, description="最大金额筛选"),
    transaction_type: Optional[str] = Query(None, description="交易类型筛选：income, expense, transfer"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(50, description="每页条数", ge=1, le=200)
):
    """获取交易列表"""
    try:
        filter_params = TransactionFilter(
            start_date=start_date,
            end_date=end_date,
            account=account,
            payee=payee,
            narration=narration,
            min_amount=amount_min,
            max_amount=amount_max,
            transaction_type=transaction_type
        )
        
        # 获取所有符合条件的交易
        all_transactions = beancount_service.get_transactions(filter_params)
        total_count = len(all_transactions)
        
        # 计算分页
        offset = (page - 1) * page_size
        paginated_transactions = all_transactions[offset:offset + page_size]
        
        return {
            "data": paginated_transactions,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易列表失败: {str(e)}")

@router.post("/", response_model=dict)
async def create_transaction(transaction: TransactionCreate):
    """创建新交易"""
    try:
        # 转换为字典格式
        transaction_data = {
            "date": transaction.date.isoformat(),
            "flag": transaction.flag,
            "payee": transaction.payee,
            "narration": transaction.narration,
            "tags": transaction.tags,
            "links": transaction.links,
            "postings": [
                {
                    "account": p.account,
                    "amount": float(p.amount) if p.amount else None,
                    "currency": p.currency
                }
                for p in transaction.postings
            ]
        }
        
        success = beancount_service.add_transaction(transaction_data)
        
        if success:
            return {"message": "交易创建成功", "success": True}
        else:
            raise HTTPException(status_code=400, detail="交易创建失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建交易失败: {str(e)}")

@router.get("/accounts", response_model=List[str])
async def get_accounts():
    """获取活跃账户列表（排除已归档账户）"""
    try:
        accounts = beancount_service.get_active_accounts()
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户列表失败: {str(e)}")

@router.get("/payees", response_model=List[str])
async def get_payees():
    """获取所有收付方列表"""
    try:
        payees = beancount_service.get_all_payees()
        return payees
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取收付方列表失败: {str(e)}")


@router.get("/account-journal", response_model=List[TransactionResponse])
async def get_account_journal(
    account: str = Query(..., description="账户名称"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
):
    """获取指定账户在时间范围内的所有交易记录（日记账）"""
    try:
        filter_params = TransactionFilter(
            account=account,
            start_date=start_date,
            end_date=end_date,
        )
        transactions = beancount_service.get_transactions(filter_params)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户日记账失败: {str(e)}")



@router.get("/recent", response_model=List[TransactionResponse])
async def get_recent_transactions(days: int = Query(30, description="最近天数", ge=1, le=365)):
    """获取最近的交易"""
    try:
        from datetime import datetime, timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        filter_params = TransactionFilter(
            start_date=start_date,
            end_date=end_date
        )
        
        transactions = beancount_service.get_transactions(filter_params)
        return transactions[:50]  # 最多返回50条
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近交易失败: {str(e)}")

@router.get("/{transaction_id}")
async def get_transaction_by_id(transaction_id: str):
    """根据transaction_id获取单个交易（格式：filename:lineno）"""
    try:
        if ':' not in transaction_id:
            raise HTTPException(status_code=400, detail="无效的transaction_id格式，应为 filename:lineno")
        
        # 解析transaction_id
        parts = transaction_id.split(':')
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="无效的transaction_id格式，应为 filename:lineno")
        
        filename = parts[0]
        try:
            lineno = int(parts[1])
        except ValueError:
            raise HTTPException(status_code=400, detail="行号必须是数字")
        
        # 获取交易
        transaction = beancount_service.get_transaction_by_location(filename, lineno)
        if not transaction:
            raise HTTPException(status_code=404, detail="未找到指定的交易")
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易失败: {str(e)}")

@router.put("/{transaction_id}")
async def update_transaction(transaction_id: str, transaction: TransactionCreate):
    """根据transaction_id更新交易"""
    try:
        if ':' not in transaction_id:
            raise HTTPException(status_code=400, detail="无效的transaction_id格式，应为 filename:lineno")
        
        # 解析transaction_id
        parts = transaction_id.split(':')
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="无效的transaction_id格式，应为 filename:lineno")
        
        filename = parts[0]
        try:
            lineno = int(parts[1])
        except ValueError:
            raise HTTPException(status_code=400, detail="行号必须是数字")
        
        # 转换为字典格式
        transaction_data = {
            "date": transaction.date.isoformat(),
            "flag": transaction.flag,
            "payee": transaction.payee,
            "narration": transaction.narration,
            "tags": transaction.tags,
            "links": transaction.links,
            "postings": [
                {
                    "account": p.account,
                    "amount": float(p.amount) if p.amount else None,
                    "currency": p.currency
                }
                for p in transaction.postings
            ]
        }
        
        # 更新交易
        success = beancount_service.update_transaction_by_location(filename, lineno, transaction_data)
        
        if success:
            return {"message": "交易更新成功", "success": True}
        else:
            raise HTTPException(status_code=400, detail="交易更新失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新交易失败: {str(e)}")

@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: str):
    """根据transaction_id删除交易"""
    try:
        if ':' not in transaction_id:
            raise HTTPException(status_code=400, detail="无效的transaction_id格式，应为 filename:lineno")
        
        # 解析transaction_id
        parts = transaction_id.split(':')
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="无效的transaction_id格式，应为 filename:lineno")
        
        filename = parts[0]
        try:
            lineno = int(parts[1])
        except ValueError:
            raise HTTPException(status_code=400, detail="行号必须是数字")
        
        # 删除交易
        success = beancount_service.delete_transaction_by_location(filename, lineno)
        
        if success:
            return {"message": "交易删除成功", "success": True}
        else:
            raise HTTPException(status_code=400, detail="交易删除失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除交易失败: {str(e)}") 