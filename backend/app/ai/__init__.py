"""
AgentUniverse AI 模块

提供基于 PEER 多 Agent 架构的财务分析服务：
- Planning Agent: 问题规划
- Executing Agent: 数据执行
- Expressing Agent: 结论表达
- Reviewing Agent: 质量审核

使用 Finance Master Agent 协调以上子 Agent。
"""

from app.ai.service import ai_service, AIService

__all__ = [
    "ai_service",
    "AIService",
]
