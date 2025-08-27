from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from app.models.ai_config import AIConfig
from app.models.ai_schemas import AIConfigCreate, AIConfigUpdate, DEFAULT_AI_CONFIGS
import logging

logger = logging.getLogger(__name__)


class AIConfigService:
    """AI配置服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_config(self, key: str) -> Optional[AIConfig]:
        """获取单个配置"""
        return self.db.query(AIConfig).filter(AIConfig.key == key).first()
    
    def get_all_configs(self) -> List[AIConfig]:
        """获取所有配置"""
        return self.db.query(AIConfig).all()
    
    def get_configs_dict(self) -> Dict[str, str]:
        """获取配置字典"""
        configs = self.get_all_configs()
        return {config.key: config.value or "" for config in configs}
    
    def create_config(self, config_data: AIConfigCreate) -> AIConfig:
        """创建新配置"""
        db_config = AIConfig(**config_data.model_dump())
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        logger.info(f"创建AI配置: {config_data.key}")
        return db_config
    
    def update_config(self, key: str, config_data: AIConfigUpdate) -> Optional[AIConfig]:
        """更新配置"""
        db_config = self.get_config(key)
        if not db_config:
            return None
        
        update_data = config_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_config, field, value)
        
        self.db.commit()
        self.db.refresh(db_config)
        logger.info(f"更新AI配置: {key}")
        return db_config
    
    def upsert_config(self, key: str, value: str, description: str = None) -> AIConfig:
        """创建或更新配置"""
        db_config = self.get_config(key)
        if db_config:
            db_config.value = value
            if description:
                db_config.description = description
        else:
            db_config = AIConfig(key=key, value=value, description=description)
            self.db.add(db_config)
        
        self.db.commit()
        self.db.refresh(db_config)
        return db_config
    
    def delete_config(self, key: str) -> bool:
        """删除配置"""
        db_config = self.get_config(key)
        if not db_config:
            return False
        
        self.db.delete(db_config)
        self.db.commit()
        logger.info(f"删除AI配置: {key}")
        return True
    
    def init_default_configs(self) -> None:
        """初始化默认配置"""
        logger.info("初始化默认AI配置...")
        
        for key, config_info in DEFAULT_AI_CONFIGS.items():
            existing_config = self.get_config(key)
            if not existing_config:
                self.create_config(AIConfigCreate(
                    key=key,
                    value=config_info["value"],
                    description=config_info["description"]
                ))
                logger.info(f"创建默认配置: {key}")
        
        logger.info("默认AI配置初始化完成")
    
    def validate_config(self) -> Dict[str, str]:
        """验证配置完整性"""
        errors = {}
        configs = self.get_configs_dict()
        
        # 检查必需的配置项
        required_keys = ["llm_model", "llm_api_key"]
        for key in required_keys:
            if not configs.get(key):
                errors[key] = f"配置项 {key} 是必需的"
        
        # 验证数值类型配置
        try:
            max_tokens = int(configs.get("max_tokens", "2000"))
            if max_tokens <= 0:
                errors["max_tokens"] = "max_tokens 必须是正整数"
        except ValueError:
            errors["max_tokens"] = "max_tokens 必须是有效的整数"
        
        try:
            temperature = float(configs.get("temperature", "0.7"))
            if not 0 <= temperature <= 2:
                errors["temperature"] = "temperature 必须在 0-2 之间"
        except ValueError:
            errors["temperature"] = "temperature 必须是有效的数字"
        
        return errors
