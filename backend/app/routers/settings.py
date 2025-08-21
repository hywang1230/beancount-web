from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database import get_db
from app.services.setting_service import setting_service
from pydantic import BaseModel

class SettingResponse(BaseModel):
    key: str
    value: str

    class Config:
        orm_mode = True

class SettingUpdate(BaseModel):
    value: str

router = APIRouter(prefix="/settings", tags=["应用设置"])

@router.get("/", response_model=List[SettingResponse])
async def get_all_settings(db: Session = Depends(get_db)):
    """获取所有设置"""
    settings = setting_service.get_all_settings(db=db)
    return settings

@router.put("/{key}", response_model=SettingResponse)
async def update_setting(key: str, setting_in: SettingUpdate, db: Session = Depends(get_db)):
    """更新或创建设置"""
    updated_setting = setting_service.update_setting(db=db, key=key, value=setting_in.value)
    return updated_setting
