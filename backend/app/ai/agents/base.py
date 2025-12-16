"""
Agent 组件基类

定义 AgentUniverse 风格的 Agent 基类。
"""
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class AgentInput:
    """Agent 输入数据结构"""
    
    def __init__(self, **kwargs):
        self._data = kwargs
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取输入数据"""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置数据"""
        self._data[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._data.copy()


class AgentOutput:
    """Agent 输出数据结构"""
    
    def __init__(self, **kwargs):
        self._data = kwargs
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取输出数据"""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置数据"""
        self._data[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._data.copy()
    
    @property
    def output(self) -> str:
        """获取主要输出内容"""
        return self._data.get("output", "")


class Agent(ABC):
    """
    Agent 基类
    
    AgentUniverse 风格的 Agent 基类，所有自定义 Agent 都应继承此类。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent 描述"""
        pass
    
    @abstractmethod
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """
        执行 Agent
        
        Args:
            agent_input: Agent 输入
            
        Returns:
            Agent 输出
        """
        pass
    
    async def __call__(self, **kwargs) -> AgentOutput:
        """支持直接调用"""
        agent_input = AgentInput(**kwargs)
        return await self.run(agent_input)
