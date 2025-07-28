from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date, datetime, timedelta

from app.models.schemas import BalanceResponse, IncomeStatement
from app.services.beancount_service import beancount_service

router = APIRouter()

@router.get("/balance-sheet", response_model=BalanceResponse)
async def get_balance_sheet(
    as_of_date: Optional[date] = Query(None, description="截止日期，默认为今天")
):
    """获取资产负债表"""
    try:
        if as_of_date is None:
            as_of_date = datetime.now().date()
            
        balance_sheet = beancount_service.get_balance_sheet(as_of_date)
        return balance_sheet
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资产负债表失败: {str(e)}")

@router.get("/income-statement", response_model=IncomeStatement)
async def get_income_statement(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期")
):
    """获取损益表"""
    try:
        # 默认获取当前月份的损益表
        if end_date is None:
            end_date = datetime.now().date()
        if start_date is None:
            start_date = end_date.replace(day=1)  # 当月第一天
            
        income_statement = beancount_service.get_income_statement(start_date, end_date)
        return income_statement
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取损益表失败: {str(e)}")

@router.get("/monthly-summary")
async def get_monthly_summary(
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, description="月份")
):
    """获取月度汇总报告"""
    try:
        from calendar import monthrange
        
        # 默认为当前月份
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month
        
        # 计算月份的开始和结束日期
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
        
        # 获取损益表
        income_statement = beancount_service.get_income_statement(start_date, end_date)
        
        # 获取期末资产负债表
        balance_sheet = beancount_service.get_balance_sheet(end_date)
        
        return {
            "period": f"{year}年{month}月",
            "start_date": start_date,
            "end_date": end_date,
            "income_statement": income_statement,
            "balance_sheet": balance_sheet
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取月度汇总失败: {str(e)}")

@router.get("/year-to-date")
async def get_year_to_date_summary(year: Optional[int] = Query(None, description="年份")):
    """获取年度至今汇总报告"""
    try:
        if year is None:
            year = datetime.now().year
        
        start_date = date(year, 1, 1)
        end_date = datetime.now().date()
        
        # 确保不超过当前年份
        if end_date.year > year:
            end_date = date(year, 12, 31)
        
        income_statement = beancount_service.get_income_statement(start_date, end_date)
        balance_sheet = beancount_service.get_balance_sheet(end_date)
        
        return {
            "period": f"{year}年至今",
            "start_date": start_date,
            "end_date": end_date,
            "income_statement": income_statement,
            "balance_sheet": balance_sheet
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取年度汇总失败: {str(e)}")

@router.get("/trends")
async def get_trends(
    months: int = Query(12, description="月份数", ge=3, le=24)
):
    """获取趋势分析数据"""
    try:
        from datetime import datetime, timedelta
        import calendar
        
        trends = []
        end_date = datetime.now().date()
        
        for i in range(months):
            # 计算每个月的开始和结束日期
            month_end = end_date.replace(day=1) - timedelta(days=i*30)
            month_start = month_end.replace(day=1)
            _, last_day = calendar.monthrange(month_end.year, month_end.month)
            month_actual_end = month_end.replace(day=last_day)
            
            # 获取该月的损益表
            income_statement = beancount_service.get_income_statement(month_start, month_actual_end)
            
            trends.append({
                "period": f"{month_end.year}-{month_end.month:02d}",
                "year": month_end.year,
                "month": month_end.month,
                "total_income": income_statement.total_income,
                "total_expenses": income_statement.total_expenses,
                "net_income": income_statement.net_income
            })
        
        # 按时间顺序排列
        trends.reverse()
        
        return {
            "trends": trends,
            "currency": "CNY"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势分析失败: {str(e)}") 

@router.get("/account-configuration")
async def get_account_configuration():
    """获取Beancount账户配置信息"""
    try:
        config = beancount_service.get_account_configuration()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置信息失败: {str(e)}")

@router.get("/conversion-account-info")
async def get_conversion_account_info():
    """获取转换账户的说明信息"""
    try:
        info = beancount_service.get_conversion_account_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取转换账户信息失败: {str(e)}") 