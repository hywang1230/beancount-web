"""
缓存管理模块
提供内存缓存和持久化缓存功能
"""

import hashlib
import json
import time
from datetime import datetime, date
from typing import Any, Dict, Optional, Callable, TypeVar, Generic
from functools import wraps
from pathlib import Path
import threading
import sqlite3
from decimal import Decimal

from app.core.config import settings

T = TypeVar('T')

class LRUCache(Generic[T]):
    """LRU缓存实现"""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order = []
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        with self._lock:
            if key in self.cache:
                # 更新访问顺序
                self.access_order.remove(key)
                self.access_order.append(key)
                
                # 检查TTL
                item = self.cache[key]
                if item['expires_at'] and time.time() > item['expires_at']:
                    del self.cache[key]
                    self.access_order.remove(key)
                    return None
                
                return item['value']
            return None
    
    def put(self, key: str, value: T, ttl_seconds: Optional[int] = None):
        with self._lock:
            # 计算过期时间
            expires_at = None
            if ttl_seconds:
                expires_at = time.time() + ttl_seconds
            
            # 如果已存在，更新值
            if key in self.cache:
                self.cache[key] = {'value': value, 'expires_at': expires_at}
                self.access_order.remove(key)
                self.access_order.append(key)
                return
            
            # 检查容量
            if len(self.cache) >= self.capacity:
                # 删除最少使用的项
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
            
            self.cache[key] = {'value': value, 'expires_at': expires_at}
            self.access_order.append(key)
    
    def invalidate(self, pattern: str = None):
        """使缓存失效"""
        with self._lock:
            if pattern is None:
                # 清空所有缓存
                self.cache.clear()
                self.access_order.clear()
            else:
                # 删除匹配模式的键
                keys_to_remove = [k for k in self.cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self.cache[key]
                    if key in self.access_order:
                        self.access_order.remove(key)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.memory_cache = LRUCache[Any](capacity=2000)
        self.db_path = settings.data_dir / "performance_cache.db"
        self.entries_version = 0
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """初始化缓存数据库"""
        with sqlite3.connect(self.db_path) as conn:
            # 设置时区为东八区
            conn.execute("PRAGMA timezone = '+08:00'")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    version INTEGER,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_version ON cache_entries(version)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at)
            """)
    
    def _serialize_value(self, value: Any) -> str:
        """序列化值用于存储"""
        def default_serializer(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            elif isinstance(obj, Decimal):
                return str(obj)
            elif hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)
        
        return json.dumps(value, default=default_serializer, ensure_ascii=False)
    
    def _deserialize_value(self, value_str: str) -> Any:
        """反序列化存储的值"""
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            return value_str
    
    def get(self, key: str, use_persistent: bool = True) -> Optional[Any]:
        """获取缓存值"""
        # 先检查内存缓存
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # 检查持久化缓存
        if use_persistent:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT value, version, expires_at FROM cache_entries 
                        WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
                    """, (key, settings.now().isoformat()))
                    
                    row = cursor.fetchone()
                    if row:
                        value_str, version, expires_at = row
                        # 检查版本是否有效
                        if version >= self.entries_version:
                            value = self._deserialize_value(value_str)
                            # 放入内存缓存
                            self.memory_cache.put(key, value, ttl_seconds=3600)
                            return value
            except Exception as e:
                # print(f"读取持久化缓存失败: {e}")
                pass
        
        return None
    
    def put(self, key: str, value: Any, ttl_seconds: int = 3600, use_persistent: bool = True):
        """设置缓存值"""
        # 存入内存缓存
        self.memory_cache.put(key, value, ttl_seconds)
        
        # 存入持久化缓存
        if use_persistent:
            try:
                expires_at = None
                if ttl_seconds:
                    expires_at = (settings.now().timestamp() + ttl_seconds)
                    expires_at = datetime.fromtimestamp(expires_at).isoformat()
                
                value_str = self._serialize_value(value)
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries 
                        (key, value, version, created_at, expires_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (key, value_str, self.entries_version, 
                          settings.now().isoformat(), expires_at))
            except Exception as e:
                # print(f"写入持久化缓存失败: {e}")
                pass
    
    def invalidate_by_pattern(self, pattern: str):
        """按模式使缓存失效"""
        self.memory_cache.invalidate(pattern)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries WHERE key LIKE ?", (f"%{pattern}%",))
        except Exception as e:
            # print(f"清理持久化缓存失败: {e}")
            pass
    
    def bump_version(self):
        """增加版本号，使所有缓存失效"""
        with self._lock:
            self.entries_version += 1
            self.memory_cache.invalidate()
            
            # 清理过期的持久化缓存
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        DELETE FROM cache_entries 
                        WHERE version < ? OR (expires_at IS NOT NULL AND expires_at < ?)
                    """, (self.entries_version, settings.now().isoformat()))
            except Exception as e:
                # print(f"清理过期缓存失败: {e}")
                pass
    
    def cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键"""
        # 将参数排序后生成哈希
        params_str = json.dumps(kwargs, sort_keys=True, default=str)
        hash_suffix = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{prefix}:{hash_suffix}"

# 全局缓存管理器实例
cache_manager = CacheManager()

def cached(key_prefix: str, ttl_seconds: int = 3600, use_persistent: bool = True):
    """缓存装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 生成缓存键
            cache_key = cache_manager.cache_key(key_prefix, args=args, kwargs=kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key, use_persistent)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.put(cache_key, result, ttl_seconds, use_persistent)
            
            return result
        return wrapper
    return decorator
