from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.models.auth import UserLogin, Token, User
from app.utils.auth import authenticate_user, create_access_token, get_current_user
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=Token, summary="用户登录")
async def login(user_login: UserLogin):
    """
    用户登录接口
    """
    user = authenticate_user(user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User, summary="获取当前用户信息")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息
    """
    return current_user

@router.post("/logout", summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出接口（JWT无状态，客户端删除token即可）
    """
    return {"message": "登出成功"}
