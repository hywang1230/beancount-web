"""
报表生成工具 - 封装ReportGenerator服务供AI服务使用

注意：这是简化版实现，不依赖AgentUniverse框架。
后续可以升级为完整的AgentUniverse Tool组件。
"""
from typing import Optional, Dict, Any
from datetime import datetime


class ReportTool:
    """
    报表生成工具
    
    提供财务报表生成能力，包括：
    - 资产负债表
    - 损益表
    - 月度汇总
    - 趋势分析
    """
    
    name: str = "report_tool"
    description: str = """财务报表工具，用于生成各类财务报表。
    支持的操作：
    - get_balance_sheet: 获取资产负债表，可指定截止日期
    - get_income_statement: 获取损益表，需指定开始和结束日期
    - get_monthly_summary: 获取月度汇总，可指定年月
    - get_trends: 获取趋势分析数据，可指定月份数
    """
    
    def execute(self, action: str, date: Optional[str] = None,
                start_date: Optional[str] = None, end_date: Optional[str] = None,
                year: Optional[int] = None, month: Optional[int] = None,
                months: int = 12) -> Dict[str, Any]:
        """执行报表生成"""
        from app.services.beancount_service import beancount_service
        
        try:
            if action == "get_balance_sheet":
                as_of_date = None
                if date:
                    as_of_date = datetime.strptime(date, "%Y-%m-%d").date()
                else:
                    as_of_date = datetime.now().date()
                    
                result = beancount_service.get_balance_sheet(as_of_date)
                return {
                    "success": True,
                    "report_type": "balance_sheet",
                    "as_of_date": str(as_of_date),
                    "data": self._format_balance_sheet(result)
                }
                
            elif action == "get_income_statement":
                end_dt = datetime.now().date()
                if end_date:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                    
                start_dt = end_dt.replace(day=1)
                if start_date:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                    
                result = beancount_service.get_income_statement(start_dt, end_dt)
                return {
                    "success": True,
                    "report_type": "income_statement",
                    "start_date": str(start_dt),
                    "end_date": str(end_dt),
                    "data": self._format_income_statement(result)
                }
                
            elif action == "get_monthly_summary":
                yr = year or datetime.now().year
                mo = month or datetime.now().month
                
                from calendar import monthrange
                from datetime import date as dt_date
                
                start_dt = dt_date(yr, mo, 1)
                _, last_day = monthrange(yr, mo)
                end_dt = dt_date(yr, mo, last_day)
                
                income_statement = beancount_service.get_income_statement(start_dt, end_dt)
                balance_sheet = beancount_service.get_balance_sheet(end_dt)
                
                return {
                    "success": True,
                    "report_type": "monthly_summary",
                    "period": f"{yr}年{mo}月",
                    "data": {
                        "income_statement": self._format_income_statement(income_statement),
                        "balance_sheet": self._format_balance_sheet(balance_sheet)
                    }
                }
                
            elif action == "get_trends":
                months_count = min(months, 24)
                trends = []
                end_dt = datetime.now().date()
                
                import calendar
                from datetime import timedelta, date as dt_date
                
                for i in range(months_count):
                    month_end = end_dt.replace(day=1) - timedelta(days=i*30)
                    month_start = month_end.replace(day=1)
                    _, last_day = calendar.monthrange(month_end.year, month_end.month)
                    month_actual_end = month_end.replace(day=last_day)
                    
                    income_statement = beancount_service.get_income_statement(month_start, month_actual_end)
                    
                    trends.append({
                        "period": f"{month_end.year}-{month_end.month:02d}",
                        "year": month_end.year,
                        "month": month_end.month,
                        "total_income": str(income_statement.total_income),
                        "total_expenses": str(income_statement.total_expenses),
                        "net_income": str(income_statement.net_income)
                    })
                
                trends.reverse()
                
                return {
                    "success": True,
                    "report_type": "trends",
                    "months": months_count,
                    "data": trends
                }
                
            else:
                return {
                    "success": False,
                    "error": f"不支持的操作类型: {action}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_balance_sheet(self, result) -> Dict[str, Any]:
        """格式化资产负债表"""
        return {
            "total_assets": str(result.total_assets),
            "total_liabilities": str(result.total_liabilities),
            "net_worth": str(result.net_worth),
            "currency": result.currency,
            "assets_count": len(result.assets) if result.assets else 0,
            "liabilities_count": len(result.liabilities) if result.liabilities else 0
        }
    
    def _format_income_statement(self, result) -> Dict[str, Any]:
        """格式化损益表"""
        return {
            "total_income": str(result.total_income),
            "total_expenses": str(result.total_expenses),
            "net_income": str(result.net_income),
            "currency": result.currency,
            "income_items_count": len(result.income) if result.income else 0,
            "expense_items_count": len(result.expenses) if result.expenses else 0
        }


# 工具实例
report_tool = ReportTool()
