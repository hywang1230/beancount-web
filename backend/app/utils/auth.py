from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.models.auth import TokenData, User, UserInDB

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token 安全认证
security = HTTPBearer()

# 缓存密码哈希，避免每次请求重新计算
_cached_password_hash: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[UserInDB]:
    """获取用户信息"""
    # 在实际应用中，这里应该从数据库获取用户信息
    # 这里简化处理，使用环境变量中的用户名和密码
    if username == settings.username:
        # 缓存密码哈希，避免每次请求重新计算
        global _cached_password_hash
        if _cached_password_hash is None:
            _cached_password_hash = get_password_hash(settings.password)
        return UserInDB(username=username, hashed_password=_cached_password_hash)
    return None

def authenticate_user(username: str, password: str) -> Optional[User]:
    """验证用户凭据"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return User(username=user.username)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """获取当前用户"""
    # 如果认证被禁用，直接返回默认用户
    if not settings.enable_auth:
        return User(username=settings.username)
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if credentials is None:
            raise credentials_exception
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(username=user.username)

# 创建一个可选的认证依赖，当认证被禁用时不需要token
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    """获取当前用户（可选认证）"""
    # 如果认证被禁用，直接返回默认用户
    if not settings.enable_auth:
        return User(username=settings.username)
    
    # 如果没有提供token且认证是必需的，返回None
    if credentials is None:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except JWTError:
        return None
    
    user = get_user(username=token_data.username)
    if user is None:
        return None
    return User(username=user.username)
