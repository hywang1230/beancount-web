"""
Tool 组件基类

定义 AgentUniverse 风格的 Tool 基类和输入结构。
"""
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolInput:
    """工具输入数据结构"""
    
    _data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self._data is None:
            self._data = {}
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取输入数据"""
        return self._data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置输入数据"""
        self._data[key] = value
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolInput":
        """从字典创建输入"""
        instance = cls()
        instance._data = data or {}
        return instance


class Tool(ABC):
    """
    工具基类
    
    AgentUniverse 风格的 Tool 基类，所有自定义工具都应继承此类。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @abstractmethod
    def execute(self, tool_input: ToolInput) -> Any:
        """
        执行工具
        
        Args:
            tool_input: 工具输入
            
        Returns:
            工具执行结果
        """
        pass
    
    def __call__(self, **kwargs) -> Any:
        """支持直接调用"""
        tool_input = ToolInput.from_dict(kwargs)
        return self.execute(tool_input)
