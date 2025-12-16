"""
预算查询工具 - 封装BudgetService服务供AI服务使用

注意：这是简化版实现，不依赖AgentUniverse框架。
后续可以升级为完整的AgentUniverse Tool组件。
"""
from typing import Optional, Dict, Any


class BudgetTool:
    """
    预算查询工具
    
    提供预算数据查询能力，包括：
    - 获取预算列表
    - 获取预算执行进度
    - 获取预算汇总
    """
    
    name: str = "budget_tool"
    description: str = """预算查询工具，用于获取预算数据和执行情况。
    支持的操作：
    - get_budgets: 获取预算列表
    - get_budget_progress: 获取特定预算的执行进度，需要budget_id
    - get_budget_summary: 获取预算汇总，可指定周期类型和值
    """
    
    def execute(self, action: str, budget_id: Optional[int] = None,
                period_type: str = "month", 
                period_value: Optional[str] = None) -> Dict[str, Any]:
        """执行预算查询"""
        from app.database import get_db
        from app.services.budget_service import BudgetService
        
        try:
            # 获取数据库会话
            db = next(get_db())
            budget_service = BudgetService(db)
            
            if action == "get_budgets":
                budgets = budget_service.get_budgets(
                    period_type=period_type,
                    period_value=period_value
                )
                return {
                    "success": True,
                    "count": len(budgets),
                    "budgets": [self._format_budget(b) for b in budgets]
                }
                
            elif action == "get_budget_progress":
                if not budget_id:
                    return {
                        "success": False,
                        "error": "budget_id是必需的参数"
                    }
                    
                progress = budget_service.get_budget_progress(budget_id)
                if not progress:
                    return {
                        "success": False,
                        "error": f"未找到ID为{budget_id}的预算"
                    }
                    
                return {
                    "success": True,
                    "progress": self._format_progress(progress)
                }
                
            elif action == "get_budget_summary":
                summary = budget_service.get_budget_summary(
                    period_type=period_type,
                    period_value=period_value
                )
                return {
                    "success": True,
                    "summary": self._format_summary(summary)
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
    
    def _format_budget(self, budget) -> Dict[str, Any]:
        """格式化预算数据"""
        return {
            "id": budget.id,
            "name": budget.name,
            "category": budget.category,
            "amount": str(budget.amount),
            "currency": budget.currency,
            "period_type": budget.period_type,
            "period_value": budget.period_value
        }
    
    def _format_progress(self, progress) -> Dict[str, Any]:
        """格式化预算进度"""
        return {
            "budget_name": progress.budget_name,
            "budget_amount": str(progress.budget_amount),
            "spent_amount": str(progress.spent_amount),
            "remaining_amount": str(progress.remaining_amount),
            "progress_percentage": progress.progress_percentage,
            "is_over_budget": progress.is_over_budget,
            "days_remaining": progress.days_remaining
        }
    
    def _format_summary(self, summary) -> Dict[str, Any]:
        """格式化预算汇总"""
        return {
            "total_budget": str(summary.total_budget),
            "total_spent": str(summary.total_spent),
            "total_remaining": str(summary.total_remaining),
            "overall_progress": summary.overall_progress,
            "budgets_count": summary.budgets_count,
            "over_budget_count": summary.over_budget_count
        }


# 工具实例
budget_tool = BudgetTool()
