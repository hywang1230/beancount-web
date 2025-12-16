"""
预算查询工具 - AgentUniverse Tool 实现

继承 Tool 基类，提供预算数据查询能力。
"""
from typing import Optional, Dict, Any
import logging

from app.ai.tools.base import Tool, ToolInput

logger = logging.getLogger(__name__)


class BudgetTool(Tool):
    """
    预算查询工具
    
    提供预算数据查询能力，包括：
    - get_budgets: 获取预算列表
    - get_budget_progress: 获取特定预算的执行进度
    - get_budget_summary: 获取预算汇总
    """
    
    @property
    def name(self) -> str:
        return "budget_tool"
    
    @property
    def description(self) -> str:
        return """预算查询工具，用于获取预算数据和执行情况。
支持的操作(action参数)：
- get_budgets: 获取预算列表，可选参数: period_type(默认month), period_value
- get_budget_progress: 获取特定预算执行进度，需要参数: budget_id
- get_budget_summary: 获取预算汇总，可选参数: period_type, period_value"""
    
    def execute(self, tool_input: ToolInput) -> Dict[str, Any]:
        """执行预算查询"""
        action = tool_input.get_data("action", "get_budget_summary")
        
        if action == "get_budgets":
            return self._get_budgets(tool_input)
        elif action == "get_budget_progress":
            return self._get_budget_progress(tool_input)
        elif action == "get_budget_summary":
            return self._get_budget_summary(tool_input)
        else:
            return {"success": False, "error": f"不支持的操作类型: {action}"}
    
    def _get_budgets(self, tool_input: ToolInput) -> Dict[str, Any]:
        """获取预算列表"""
        from app.database import get_db
        from app.services.budget_service import BudgetService
        
        try:
            period_type = tool_input.get_data("period_type", "month")
            period_value = tool_input.get_data("period_value")
            
            db = next(get_db())
            budget_service = BudgetService(db)
            
            budgets = budget_service.get_budgets(
                period_type=period_type,
                period_value=period_value
            )
            
            return {
                "success": True,
                "count": len(budgets),
                "budgets": [self._format_budget(b) for b in budgets]
            }
        except Exception as e:
            logger.error(f"获取预算列表失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_budget_progress(self, tool_input: ToolInput) -> Dict[str, Any]:
        """获取预算执行进度"""
        from app.database import get_db
        from app.services.budget_service import BudgetService
        
        try:
            budget_id = tool_input.get_data("budget_id")
            if not budget_id:
                return {"success": False, "error": "budget_id是必需的参数"}
            
            db = next(get_db())
            budget_service = BudgetService(db)
            
            progress = budget_service.get_budget_progress(budget_id)
            if not progress:
                return {"success": False, "error": f"未找到ID为{budget_id}的预算"}
            
            return {
                "success": True,
                "progress": self._format_progress(progress)
            }
        except Exception as e:
            logger.error(f"获取预算进度失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_budget_summary(self, tool_input: ToolInput) -> Dict[str, Any]:
        """获取预算汇总"""
        from app.database import get_db
        from app.services.budget_service import BudgetService
        
        try:
            period_type = tool_input.get_data("period_type", "month")
            period_value = tool_input.get_data("period_value")
            
            db = next(get_db())
            budget_service = BudgetService(db)
            
            summary = budget_service.get_budget_summary(
                period_type=period_type,
                period_value=period_value
            )
            
            return {
                "success": True,
                "summary": self._format_summary(summary)
            }
        except Exception as e:
            logger.error(f"获取预算汇总失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_budget(self, budget) -> Dict[str, Any]:
        """格式化预算数据"""
        return {
            "id": budget.id,
            "name": budget.name,
            "category": budget.category,
            "amount": float(budget.amount),
            "currency": budget.currency,
            "period_type": budget.period_type,
            "period_value": budget.period_value
        }
    
    def _format_progress(self, progress) -> Dict[str, Any]:
        """格式化预算进度"""
        return {
            "budget_name": progress.budget_name,
            "budget_amount": float(progress.budget_amount),
            "spent_amount": float(progress.spent_amount),
            "remaining_amount": float(progress.remaining_amount),
            "progress_percentage": progress.progress_percentage,
            "is_over_budget": progress.is_over_budget,
            "days_remaining": progress.days_remaining
        }
    
    def _format_summary(self, summary) -> Dict[str, Any]:
        """格式化预算汇总"""
        # 计算超支预算数量
        over_budget_count = sum(1 for b in summary.budgets if b.is_exceeded)
        
        return {
            "total_budget": float(summary.total_budget),
            "total_spent": float(summary.total_spent),
            "total_remaining": float(summary.total_remaining),
            "overall_progress": summary.overall_percentage,  # 使用正确的属性名
            "budgets_count": len(summary.budgets),           # 从列表计算
            "over_budget_count": over_budget_count,          # 计算超支数量
            "currency": summary.currency
        }


# 工具实例
budget_tool = BudgetTool()
