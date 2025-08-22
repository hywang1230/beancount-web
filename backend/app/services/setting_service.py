from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.setting import Setting as SettingModel

class SettingService:
    def get_setting(self, db: Session, key: str) -> Optional[SettingModel]:
        """获取单个设置"""
        return db.query(SettingModel).filter(SettingModel.key == key).first()

    def get_all_settings(self, db: Session) -> List[SettingModel]:
        """获取所有设置"""
        return db.query(SettingModel).all()

    def update_setting(self, db: Session, key: str, value: str) -> SettingModel:
        """更新或创建设置"""
        db_setting = self.get_setting(db, key)
        if db_setting:
            db_setting.value = value
        else:
            db_setting = SettingModel(key=key, value=value)
            db.add(db_setting)
        
        db.commit()
        db.refresh(db_setting)
        return db_setting

setting_service = SettingService()
