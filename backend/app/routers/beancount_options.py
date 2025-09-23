"""
Beancount 选项和价格管理路由
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import date

from app.models.schemas import (
    OperatingCurrencyResponse, OperatingCurrencyUpdate,
    PriceCreate, PriceResponse, PriceFilter
)
from app.services.ledger_options_service import LedgerOptionsService
from app.services.ledger_loader import LedgerLoader
from app.utils.auth import get_current_user

# 创建路由和服务实例
router = APIRouter()
ledger_loader = LedgerLoader()
options_service = LedgerOptionsService(ledger_loader)


@router.get("/operating_currency", response_model=OperatingCurrencyResponse)
async def get_operating_currency():
    """获取当前主币种"""
    try:
        operating_currency = options_service.get_operating_currency()
        return OperatingCurrencyResponse(operating_currency=operating_currency)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取主币种失败: {str(e)}")


@router.put("/operating_currency")
async def update_operating_currency(
    update_data: OperatingCurrencyUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新主币种"""
    try:
        success = options_service.update_operating_currency(update_data.operating_currency)
        if success:
            return {"message": f"主币种已更新为 {update_data.operating_currency}", "success": True}
        else:
            raise HTTPException(status_code=400, detail="更新主币种失败")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新主币种失败: {str(e)}")


@router.get("/prices", response_model=PriceResponse)
async def get_prices(
    from_currency: Optional[str] = Query(None, description="源货币筛选"),
    to_currency: Optional[str] = Query(None, description="目标货币筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    price_date: Optional[date] = Query(None, description="特定日期"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(50, description="每页条数", ge=1, le=200)
):
    """获取价格列表"""
    try:
        filter_params = PriceFilter(
            from_currency=from_currency,
            to_currency=to_currency,
            start_date=start_date,
            end_date=end_date,
            price_date=price_date
        )
        
        prices, total = options_service.get_prices(filter_params, page, page_size)
        
        return PriceResponse(
            prices=prices,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取价格列表失败: {str(e)}")


@router.post("/prices")
async def create_price(
    price_data: PriceCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建或更新价格"""
    try:
        success = options_service.add_price(
            date_=price_data.entry_date,
            from_currency=price_data.from_currency,
            to_currency=price_data.to_currency,
            rate=price_data.rate
        )
        
        if success:
            return {
                "message": f"价格已保存: {price_data.entry_date} {price_data.from_currency} -> {price_data.to_currency or '主币种'}",
                "success": True
            }
        else:
            raise HTTPException(status_code=400, detail="保存价格失败")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存价格失败: {str(e)}")


@router.delete("/prices")
async def delete_price(
    date: date = Query(..., description="价格日期"),
    from_currency: str = Query(..., description="源货币"),
    to_currency: Optional[str] = Query(None, description="目标货币，默认为主币种"),
    current_user: dict = Depends(get_current_user)
):
    """删除价格"""
    try:
        success = options_service.delete_price(
            date_=date,
            from_currency=from_currency,
            to_currency=to_currency
        )
        
        if success:
            return {
                "message": f"价格已删除: {date} {from_currency} -> {to_currency or '主币种'}",
                "success": True
            }
        else:
            raise HTTPException(status_code=404, detail="未找到指定的价格")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除价格失败: {str(e)}")


@router.get("/prices/effective_rate")
async def get_effective_rate(
    date: date = Query(..., description="查询日期"),
    from_currency: str = Query(..., description="源货币"),
    to_currency: Optional[str] = Query(None, description="目标货币，默认为主币种")
):
    """获取指定日期的有效汇率"""
    try:
        rate = options_service.get_effective_rate(
            date_=date,
            from_currency=from_currency,
            to_currency=to_currency
        )
        
        if rate is not None:
            return {
                "rate": float(rate),
                "date": date,
                "from_currency": from_currency,
                "to_currency": to_currency or options_service.get_operating_currency()
            }
        else:
            return {
                "rate": None,
                "message": "未找到有效汇率",
                "date": date,
                "from_currency": from_currency,
                "to_currency": to_currency or options_service.get_operating_currency()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取有效汇率失败: {str(e)}")
