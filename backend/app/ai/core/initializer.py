"""
AgentUniverse 核心初始化模块

负责初始化 AgentUniverse 框架，加载配置和注册组件。
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# AgentUniverse 是否已初始化
_initialized = False


def get_config_path() -> Path:
    """获取配置文件路径"""
    return Path(__file__).parent.parent / "config"


def get_agent_path() -> Path:
    """获取 Agent 配置路径"""
    return Path(__file__).parent.parent / "agents"


def get_tool_path() -> Path:
    """获取 Tool 配置路径"""
    return Path(__file__).parent.parent / "tools"


def get_llm_path() -> Path:
    """获取 LLM 配置路径"""
    return Path(__file__).parent.parent / "llm"


def init_agentuniverse() -> bool:
    """
    初始化 AgentUniverse 框架
    
    Returns:
        是否成功初始化
    """
    global _initialized
    
    if _initialized:
        logger.info("AgentUniverse 已初始化，跳过")
        return True
    
    try:
        from agentuniverse.base.agentuniverse import AgentUniverse
        
        # 获取配置路径
        config_path = get_config_path()
        
        # 初始化 AgentUniverse
        au = AgentUniverse()
        au.start(config_path=str(config_path))
        
        _initialized = True
        logger.info("AgentUniverse 初始化成功")
        return True
        
    except ImportError as e:
        logger.warning(f"AgentUniverse 未安装或导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"AgentUniverse 初始化失败: {e}")
        return False


def is_initialized() -> bool:
    """检查是否已初始化"""
    return _initialized
