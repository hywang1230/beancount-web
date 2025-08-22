from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.github_sync_service import GitHubSyncService
from app.services.scheduler import scheduler

from typing import List, Optional
from datetime import date, datetime

from app.models.schemas import TransactionResponse, TransactionCreate, TransactionFilter
from app.services.beancount_service import beancount_service
from app.services.yearly_file_manager import yearly_file_manager
from app.utils.auth import get_current_user
from app.core.config import settings

router = APIRouter()

async def add_transaction_to_yearly_file(transaction_data: dict) -> bool:
    """
    将交易添加到对应年份的文件中
    
    Args:
        transaction_data: 交易数据字典
        
    Returns:
        bool: 是否成功添加
    """
    try:
        # 解析交易日期
        transaction_date = date.fromisoformat(transaction_data["date"])
        
        # 生成Beancount格式的交易内容
        transaction_content = format_transaction_content(transaction_data)
        
        # 添加到年份文件
        success = yearly_file_manager.add_transaction_to_yearly_file(
            transaction_date, transaction_content
        )
        
        return success
    except Exception as e:
        print(f"添加交易到年份文件失败: {e}")
        return False

def format_transaction_content(transaction_data: dict) -> str:
    """
    将交易数据格式化为Beancount格式
    
    Args:
        transaction_data: 交易数据字典
        
    Returns:
        str: Beancount格式的交易内容
    """
    lines = []
    
    # 交易头部
    date_str = transaction_data["date"]
    flag = transaction_data.get("flag", "*")
    payee = transaction_data.get("payee", "")
    narration = transaction_data.get("narration", "")
    
    # 构建头部行
    header_parts = [date_str, flag]
    if payee:
        header_parts.append(f'"{payee}"')
    if narration:
        header_parts.append(f'"{narration}"')
    
    lines.append(" ".join(header_parts))
    
    # 添加标签和链接
    tags = transaction_data.get("tags", [])
    links = transaction_data.get("links", [])
    
    if tags or links:
        metadata_parts = []
        if tags:
            metadata_parts.extend([f"#{tag}" for tag in tags])
        if links:
            metadata_parts.extend([f"^{link}" for link in links])
        if metadata_parts:
            lines[-1] += " " + " ".join(metadata_parts)
    
    # 添加记账分录
    postings = transaction_data.get("postings", [])
    for posting in postings:
        account = posting["account"]
        amount = posting.get("amount")
        currency = posting.get("currency", "CNY")
        
        if amount is not None:
            # 格式化金额，保留2位小数
            amount_str = f"{amount:.2f}"
            posting_line = f"  {account}  {amount_str} {currency}"
        else:
            posting_line = f"  {account}"
        
        lines.append(posting_line)
    
    return "\n".join(lines)

def schedule_delayed_sync(db: Session):
    """安排延迟同步任务，避免频繁触发同步"""
    try:
        # 使用配置的延迟时间
        scheduler.schedule_delayed_sync(db, delay_seconds=settings.sync_delay_seconds)
    except Exception as e:
        print(f"安排延迟同步失败: {e}")

# 保留原函数用于向后兼容，但标记为已弃用
async def trigger_auto_sync(db: Session):
    """Helper function to run sync in the background.
    
    @deprecated: 使用 schedule_delayed_sync 替代以避免频繁同步
    """
    sync_service = GitHubSyncService(db=db)
    config = await sync_service.get_config()
    if config and config.auto_sync:
        try:
            print("Auto-sync triggered by transaction change.")
            await sync_service._auto_sync()
        except Exception as e:
            print(f"Background auto-sync failed: {e}")


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

@router.post("/validate", response_model=dict)
async def validate_transaction(transaction: TransactionCreate):
    """校验交易数据但不保存"""
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
        
        # 校验交易数据
        validation_result = beancount_service.validate_transaction(transaction_data)
        
        return validation_result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"校验交易失败: {str(e)}")

@router.post("/", response_model=dict)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
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
        
        # 使用年份文件管理器添加交易
        success = await add_transaction_to_yearly_file(transaction_data)
        
        if success:
            # 重新加载beancount数据以包含新交易
            beancount_service.loader.load_entries(force_reload=True)
            
            # 安排延迟同步任务，避免频繁同步
            schedule_delayed_sync(db)
            return {"message": "交易创建成功", "success": True}
        else:
            raise HTTPException(status_code=400, detail="交易创建失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建交易失败: {str(e)}")

@router.get("/accounts", response_model=List[str])
async def get_accounts():
    """获取活跃账户列表（排除已归档账户）"""
    try:
        from app.services.account_order_service import account_order_service
        accounts = beancount_service.get_active_accounts()
        # 应用排序
        sorted_accounts = account_order_service.sort_accounts(accounts)
        return sorted_accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户列表失败: {str(e)}")

@router.get("/years", response_model=List[int])
async def get_available_years():
    """获取所有可用的年份文件"""
    try:
        years = yearly_file_manager.get_available_years()
        # 包含当前年份（即使文件不存在）
        current_year = datetime.now().year
        if current_year not in years:
            years.append(current_year)
        return sorted(years, reverse=True)  # 按年份倒序排列
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取年份列表失败: {str(e)}")

@router.post("/years/{year}/create")
async def create_yearly_file(year: int):
    """创建指定年份的文件"""
    try:
        yearly_file = yearly_file_manager.ensure_yearly_file_exists(year)
        return {
            "message": f"{year}年文件创建成功",
            "filename": yearly_file.name,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建年份文件失败: {str(e)}")

@router.post("/migrate-by-year")
async def migrate_transactions_by_year():
    """将主文件中的交易按年份迁移到对应的年份文件"""
    try:
        success = yearly_file_manager.migrate_transactions_by_year()
        if success:
            # 重新加载beancount数据
            beancount_service.loader.load_entries(force_reload=True)
            return {"message": "交易迁移成功", "success": True}
        else:
            raise HTTPException(status_code=400, detail="交易迁移失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"迁移交易失败: {str(e)}")

@router.delete("/years/cleanup")
async def cleanup_empty_yearly_files():
    """清理空的年份文件"""
    try:
        cleaned_count = yearly_file_manager.cleanup_empty_yearly_files()
        return {
            "message": f"清理了 {cleaned_count} 个空文件",
            "cleaned_count": cleaned_count,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理文件失败: {str(e)}")

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
async def update_transaction(
    transaction_id: str, 
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
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
            # 安排延迟同步任务
            schedule_delayed_sync(db)
            return {"message": "交易更新成功", "success": True}
        else:
            raise HTTPException(status_code=400, detail="交易更新失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新交易失败: {str(e)}")

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
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
            # 安排延迟同步任务
            schedule_delayed_sync(db)
            return {"message": "交易删除成功", "success": True}
        else:
            raise HTTPException(status_code=400, detail="交易删除失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除交易失败: {str(e)}") 