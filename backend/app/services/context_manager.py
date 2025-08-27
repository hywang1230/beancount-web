from typing import List, Dict, Any, Optional, Union
import logging
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from app.services.ai_config_service import AIConfigService

logger = logging.getLogger(__name__)


class ContextManager:
    """AI聊天上下文管理器
    
    基于LangChain的内存组件，为AI聊天提供上下文感知能力。
    支持多种记忆策略：缓冲记忆等。
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.config_service = AIConfigService(db)
        self._memory_cache: Dict[str, Any] = {}  # 会话内存缓存
        self._conversation_cache: Dict[str, datetime] = {}  # 会话活跃时间缓存
        self._cache_timeout = timedelta(hours=2)  # 缓存超时时间
    
    def get_context_config(self) -> Dict[str, str]:
        """获取上下文相关配置"""
        configs = self.config_service.get_configs_dict()
        return {
            "enabled": configs.get("context_enabled", "true").lower() == "true",
            "memory_type": "buffer",  # 固定为缓冲记忆
            "buffer_window": int(configs.get("context_buffer_window", "10"))
        }
    
    def create_conversation_id(self) -> str:
        """创建新的对话ID"""
        conversation_id = str(uuid.uuid4())
        self._conversation_cache[conversation_id] = datetime.now()
        logger.info(f"创建新对话会话: {conversation_id}")
        return conversation_id
    
    def get_or_create_memory(self, conversation_id: Optional[str] = None) -> tuple[str, Any]:
        """获取或创建指定会话的内存对象
        
        Args:
            conversation_id: 会话ID，如果为None则创建新会话
            
        Returns:
            tuple: (会话ID, 内存对象)
        """
        config = self.get_context_config()
        
        # 如果禁用了上下文功能，返回空内存
        if not config["enabled"]:
            return conversation_id or self.create_conversation_id(), None
        
        # 如果没有提供会话ID，创建新会话
        if not conversation_id:
            conversation_id = self.create_conversation_id()
        
        # 检查缓存中是否存在该会话的内存
        if conversation_id in self._memory_cache:
            # 检查缓存是否过期
            if conversation_id in self._conversation_cache:
                last_active = self._conversation_cache[conversation_id]
                if datetime.now() - last_active < self._cache_timeout:
                    # 更新活跃时间
                    self._conversation_cache[conversation_id] = datetime.now()
                    return conversation_id, self._memory_cache[conversation_id]
        
        # 创建新的内存对象
        memory = self._create_memory_instance(config)
        
        # 缓存内存对象
        self._memory_cache[conversation_id] = memory
        self._conversation_cache[conversation_id] = datetime.now()
        
        logger.info(f"为会话 {conversation_id} 创建了 {config['memory_type']} 类型的内存")
        return conversation_id, memory
    
    def _create_memory_instance(self, config: Dict[str, Any]):
        """根据配置创建内存实例"""
        try:
            # 只支持缓冲记忆：保持最近N条消息
            return ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                k=config["buffer_window"]
            )
        
        except Exception as e:
            logger.error(f"创建内存实例失败: {e}，使用默认缓冲记忆")
            return ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                k=5  # 默认保持5条消息
            )
    
    def load_chat_history(self, conversation_id: str, chat_history: List[Dict[str, Any]]) -> bool:
        """从聊天历史加载到内存
        
        Args:
            conversation_id: 会话ID
            chat_history: 聊天历史列表，格式为 [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            bool: 是否成功加载
        """
        try:
            if conversation_id not in self._memory_cache:
                logger.warning(f"会话 {conversation_id} 的内存不存在")
                return False
            
            memory = self._memory_cache[conversation_id]
            if not memory:
                return False  # 上下文功能被禁用
            
            # 将聊天历史转换为LangChain消息格式
            for msg in chat_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user":
                    memory.chat_memory.add_user_message(content)
                elif role == "assistant":
                    memory.chat_memory.add_ai_message(content)
            
            logger.info(f"为会话 {conversation_id} 加载了 {len(chat_history)} 条历史消息")
            return True
            
        except Exception as e:
            logger.error(f"加载聊天历史失败: {e}")
            return False
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """添加消息到会话内存
        
        Args:
            conversation_id: 会话ID
            role: 消息角色 ("user" 或 "assistant")
            content: 消息内容
            
        Returns:
            bool: 是否成功添加
        """
        try:
            if conversation_id not in self._memory_cache:
                logger.warning(f"会话 {conversation_id} 的内存不存在")
                return False
            
            memory = self._memory_cache[conversation_id]
            if not memory:
                return False  # 上下文功能被禁用
            
            if role == "user":
                memory.chat_memory.add_user_message(content)
            elif role == "assistant":
                memory.chat_memory.add_ai_message(content)
            else:
                logger.warning(f"未知的消息角色: {role}")
                return False
            
            # 更新活跃时间
            self._conversation_cache[conversation_id] = datetime.now()
            
            logger.debug(f"向会话 {conversation_id} 添加了 {role} 消息")
            return True
            
        except Exception as e:
            logger.error(f"添加消息失败: {e}")
            return False
    
    def get_memory_variables(self, conversation_id: str) -> Dict[str, Any]:
        """获取内存变量用于构建对话上下文
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            dict: 内存变量字典
        """
        try:
            if conversation_id not in self._memory_cache:
                return {}
            
            memory = self._memory_cache[conversation_id]
            if not memory:
                return {}
            
            return memory.load_memory_variables({})
            
        except Exception as e:
            logger.error(f"获取内存变量失败: {e}")
            return {}
    

    
    def clear_conversation(self, conversation_id: str) -> bool:
        """清除指定会话的内存
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            bool: 是否成功清除
        """
        try:
            if conversation_id in self._memory_cache:
                del self._memory_cache[conversation_id]
            
            if conversation_id in self._conversation_cache:
                del self._conversation_cache[conversation_id]
            
            logger.info(f"已清除会话 {conversation_id} 的内存")
            return True
            
        except Exception as e:
            logger.error(f"清除会话内存失败: {e}")
            return False
    
    def cleanup_expired_conversations(self) -> int:
        """清理过期的会话缓存
        
        Returns:
            int: 清理的会话数量
        """
        try:
            current_time = datetime.now()
            expired_conversations = []
            
            for conversation_id, last_active in self._conversation_cache.items():
                if current_time - last_active > self._cache_timeout:
                    expired_conversations.append(conversation_id)
            
            for conversation_id in expired_conversations:
                self.clear_conversation(conversation_id)
            
            if expired_conversations:
                logger.info(f"清理了 {len(expired_conversations)} 个过期会话")
            
            return len(expired_conversations)
            
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """获取会话统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            "context_enabled": self.get_context_config()["enabled"]
        }
