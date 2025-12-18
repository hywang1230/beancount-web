"""
Agent 组件基类

定义 AgentUniverse 风格的 Agent 基类。
"""
from typing import Any, Dict, Optional
from pathlib import Path
import yaml
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


class Agent:
    """
    Agent 基类
    
    AgentUniverse 风格的 Agent 基类，所有自定义 Agent 都应继承此类。
    """
    
    def __init__(self):
        """初始化 Agent"""
        self._config = None
    
    @property
    def name(self) -> str:
        """Agent 名称"""
        raise NotImplementedError
    
    @property
    def description(self) -> str:
        """Agent 描述"""
        raise NotImplementedError
    
    def _load_config(self) -> Dict[str, Any]:
        """
        从 YAML 文件加载 Agent 配置
        约定：配置文件名为 {agent_name}.yaml，位于同一目录
        
        Returns:
            配置字典
        """
        if self._config is not None:
            return self._config
            
        try:
            config_dir = Path(__file__).parent
            config_file = config_dir / f"{self.name}.yaml"
            
            if not config_file.exists():
                logger.warning(f"配置文件不存在: {config_file}")
                self._config = {}
                return self._config
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            
            logger.debug(f"[{self.name}] 配置加载成功: {config_file}")
            return self._config
        except Exception as e:
            logger.error(f"[{self.name}] 配置加载失败: {e}")
            self._config = {}
            return self._config
    
    def _get_llm_params(self) -> Dict[str, Any]:
        """
        获取 LLM 调用参数
        从配置文件的 llm_config 字段读取
        
        Returns:
            LLM 参数字典，包含 temperature、max_tokens 等
        """
        config = self._load_config()
        default_params = {
            'temperature': 0.7,
            'max_tokens': 2000
        }
        return config.get('llm_config', default_params)
    
    def _get_profile(self) -> Dict[str, Any]:
        """
        获取 Agent 的 profile 配置
        
        Returns:
            profile 字典，包含 introduction、target、instruction 等
        """
        config = self._load_config()
        return config.get('profile', {})
    
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
