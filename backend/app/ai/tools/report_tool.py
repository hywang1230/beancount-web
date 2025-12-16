"""
报表生成工具 - AgentUniverse Tool 实现

继承 Tool 基类，提供财务报表生成能力。
"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import calendar

from app.ai.tools.base import Tool, ToolInput

logger = logging.getLogger(__name__)


class ReportTool(Tool):
    """
    报表生成工具
    
    提供财务报表生成能力，包括：
    - get_balance_sheet: 获取资产负债表
    - get_income_statement: 获取损益表
    - get_monthly_summary: 获取月度汇总
    - get_trends: 获取趋势分析数据
    """
    
    @property
    def name(self) -> str:
        return "report_tool"
    
    @property
    def description(self) -> str:
        return """财务报表工具，用于生成各类财务报表。
支持的操作(action参数)：
- get_balance_sheet: 获取资产负债表，可选参数: date(截止日期，格式YYYY-MM-DD)
- get_income_statement: 获取损益表，可选参数: start_date, end_date
- get_monthly_summary: 获取月度汇总，可选参数: year, month
- get_trends: 获取趋势分析数据，可选参数: months(月份数，默认12)"""
    
    def execute(self, tool_input: ToolInput) -> Dict[str, Any]:
        """执行报表生成"""
        action = tool_input.get_data("action", "get_monthly_summary")
        
        if action == "get_balance_sheet":
            return self._get_balance_sheet(tool_input)
        elif action == "get_income_statement":
            return self._get_income_statement(tool_input)
        elif action == "get_monthly_summary":
            return self._get_monthly_summary(tool_input)
        elif action == "get_trends":
            return self._get_trends(tool_input)
        else:
            return {"success": False, "error": f"不支持的操作类型: {action}"}
    
    def _get_balance_sheet(self, tool_input: ToolInput) -> Dict[str, Any]:
        """获取资产负债表"""
        from app.services.beancount_service import beancount_service
        
        try:
            date_str = tool_input.get_data("date")
            if date_str:
                as_of_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                as_of_date = datetime.now().date()
            
            result = beancount_service.get_balance_sheet(as_of_date)
            
            return {
                "success": True,
                "report_type": "balance_sheet",
                "as_of_date": str(as_of_date),
                "data": {
                    "total_assets": float(result.total_assets),
                    "total_liabilities": float(result.total_liabilities),
                    "net_worth": float(result.net_worth),
                    "currency": result.currency,
                    "assets_count": len(result.assets) if result.assets else 0,
                    "liabilities_count": len(result.liabilities) if result.liabilities else 0
                }
            }
        except Exception as e:
            logger.error(f"获取资产负债表失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_income_statement(self, tool_input: ToolInput) -> Dict[str, Any]:
        """获取损益表"""
        from app.services.beancount_service import beancount_service
        
        try:
            end_date_str = tool_input.get_data("end_date")
            start_date_str = tool_input.get_data("start_date")
            
            end_dt = datetime.now().date()
            if end_date_str:
                end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            
            start_dt = end_dt.replace(day=1)
            if start_date_str:
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            
            result = beancount_service.get_income_statement(start_dt, end_dt)
            
            return {
                "success": True,
                "report_type": "income_statement",
                "start_date": str(start_dt),
                "end_date": str(end_dt),
                "data": {
                    "total_income": float(result.total_income),
                    "total_expenses": float(result.total_expenses),
                    "net_income": float(result.net_income),
                    "currency": result.currency,
                    "income_items_count": len(result.income) if result.income else 0,
                    "expense_items_count": len(result.expenses) if result.expenses else 0
                }
            }
        except Exception as e:
            logger.error(f"获取损益表失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_monthly_summary(self, tool_input: ToolInput) -> Dict[str, Any]:
        """获取月度汇总"""
        from app.services.beancount_service import beancount_service
        from datetime import date as dt_date
        
        try:
            year = tool_input.get_data("year") or datetime.now().year
            month = tool_input.get_data("month") or datetime.now().month
            
            start_dt = dt_date(year, month, 1)
            _, last_day = calendar.monthrange(year, month)
            end_dt = dt_date(year, month, last_day)
            
            income_statement = beancount_service.get_income_statement(start_dt, end_dt)
            balance_sheet = beancount_service.get_balance_sheet(end_dt)
            
            return {
                "success": True,
                "report_type": "monthly_summary",
                "period": f"{year}年{month}月",
                "data": {
                    "income_statement": {
                        "total_income": float(income_statement.total_income),
                        "total_expenses": float(income_statement.total_expenses),
                        "net_income": float(income_statement.net_income),
                        "currency": income_statement.currency
                    },
                    "balance_sheet": {
                        "total_assets": float(balance_sheet.total_assets),
                        "total_liabilities": float(balance_sheet.total_liabilities),
                        "net_worth": float(balance_sheet.net_worth),
                        "currency": balance_sheet.currency
                    }
                }
            }
        except Exception as e:
            logger.error(f"获取月度汇总失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_trends(self, tool_input: ToolInput) -> Dict[str, Any]:
        """获取趋势分析数据"""
        from app.services.beancount_service import beancount_service
        from datetime import date as dt_date, timedelta
        
        try:
            months_count = min(tool_input.get_data("months", 12), 24)
            trends = []
            end_dt = datetime.now().date()
            
            for i in range(months_count):
                # 计算每个月的日期范围
                month_end = end_dt.replace(day=1) - timedelta(days=i * 30)
                month_start = month_end.replace(day=1)
                _, last_day = calendar.monthrange(month_end.year, month_end.month)
                month_actual_end = month_end.replace(day=last_day)
                
                income_statement = beancount_service.get_income_statement(month_start, month_actual_end)
                
                trends.append({
                    "period": f"{month_end.year}-{month_end.month:02d}",
                    "year": month_end.year,
                    "month": month_end.month,
                    "total_income": float(income_statement.total_income),
                    "total_expenses": float(income_statement.total_expenses),
                    "net_income": float(income_statement.net_income)
                })
            
            trends.reverse()
            
            return {
                "success": True,
                "report_type": "trends",
                "months": months_count,
                "data": trends
            }
        except Exception as e:
            logger.error(f"获取趋势数据失败: {e}")
            return {"success": False, "error": str(e)}


# 工具实例
report_tool = ReportTool()
