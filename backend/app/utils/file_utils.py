"""
文件处理工具模块
提供Beancount文件格式检查和处理功能
"""

from pathlib import Path
from typing import List

# Beancount支持的文件扩展名
BEANCOUNT_EXTENSIONS = ['.beancount', '.bean']

def is_beancount_file(filename: str) -> bool:
    """
    检查文件是否为Beancount文件
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否为Beancount文件
    """
    return any(filename.endswith(ext) for ext in BEANCOUNT_EXTENSIONS)

def get_beancount_files(directory: Path) -> List[Path]:
    """
    获取目录下所有Beancount文件
    
    Args:
        directory: 目录路径
        
    Returns:
        List[Path]: Beancount文件路径列表
    """
    files = []
    if directory.exists():
        for extension in BEANCOUNT_EXTENSIONS:
            pattern = f"*{extension}"
            files.extend(directory.glob(pattern))
    
    return [f for f in files if f.is_file()]

def get_file_extension_pattern() -> str:
    """
    获取用于文件选择器的扩展名模式
    
    Returns:
        str: 文件扩展名模式，如 ".beancount,.bean"
    """
    return ",".join(BEANCOUNT_EXTENSIONS)

def validate_file_extension(filename: str) -> bool:
    """
    验证文件扩展名是否有效
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 扩展名是否有效
    """
    return is_beancount_file(filename)

def get_backup_filename(filepath: Path) -> Path:
    """
    生成备份文件名
    
    Args:
        filepath: 原文件路径
        
    Returns:
        Path: 备份文件路径
    """
    return filepath.with_suffix(filepath.suffix + '.backup') 