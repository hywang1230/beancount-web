"""
文件处理工具模块
提供Beancount文件格式检查和处理功能
"""

from pathlib import Path
from typing import List, Dict, Set
import re

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


def parse_include_directives(content: str, base_dir: Path) -> List[Path]:
    """
    解析Beancount文件中的include指令，返回被包含的文件路径列表
    
    Args:
        content: 文件内容
        base_dir: 文件所在目录
        
    Returns:
        List[Path]: 被包含的文件路径列表
    """
    includes = []
    # 匹配 include "path" 和 include 'path' 格式
    include_pattern = r'^\s*include\s+["\']([^"\']+)["\']'
    
    for line in content.split('\n'):
        match = re.match(include_pattern, line.strip())
        if match:
            include_path = match.group(1)
            # 解析相对路径
            full_path = base_dir / include_path
            includes.append(full_path.resolve())
    
    return includes


def build_file_tree(main_file: Path, visited: Set[Path] = None) -> Dict:
    """
    构建Beancount文件的include依赖树
    
    Args:
        main_file: 主文件路径
        visited: 已访问的文件集合，用于防止循环引用
        
    Returns:
        Dict: 文件树结构
    """
    if visited is None:
        visited = set()
    
    # 防止循环引用
    if main_file in visited:
        return {
            "name": main_file.name,
            "path": str(main_file),
            "size": 0,
            "type": "file",
            "is_main": False,
            "includes": [],
            "error": "循环引用"
        }
    
    visited.add(main_file)
    
    try:
        stat = main_file.stat()
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析include指令
        includes = parse_include_directives(content, main_file.parent)
        
        # 递归构建子文件树
        children = []
        for include_file in includes:
            if include_file.exists():
                child_tree = build_file_tree(include_file, visited.copy())
                children.append(child_tree)
            else:
                # 文件不存在的情况
                children.append({
                    "name": include_file.name,
                    "path": str(include_file),
                    "size": 0,
                    "type": "file",
                    "is_main": False,
                    "includes": [],
                    "error": "文件不存在"
                })
        
        return {
            "name": main_file.name,
            "path": str(main_file),
            "size": stat.st_size,
            "type": "file",
            "is_main": True if main_file.name == "main.beancount" else False,
            "includes": children,
            "modified": stat.st_mtime
        }
        
    except Exception as e:
        return {
            "name": main_file.name,
            "path": str(main_file),
            "size": 0,
            "type": "file",
            "is_main": False,
            "includes": [],
            "error": str(e)
        }


def get_all_included_files(main_file: Path) -> List[Path]:
    """
    获取主文件及其所有include的文件列表（扁平化）
    
    Args:
        main_file: 主文件路径
        
    Returns:
        List[Path]: 所有相关文件的路径列表
    """
    all_files = []
    visited = set()
    
    def collect_files(file_path: Path):
        if file_path in visited or not file_path.exists():
            return
        
        visited.add(file_path)
        all_files.append(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            includes = parse_include_directives(content, file_path.parent)
            for include_file in includes:
                collect_files(include_file)
        except Exception:
            # 忽略读取错误，只收集能读取的文件
            pass
    
    collect_files(main_file)
    return all_files


def get_yearly_filename(year: int) -> str:
    """
    生成年份文件名
    
    Args:
        year: 年份
        
    Returns:
        str: 年份文件名
    """
    return f"transactions_{year}.beancount"


def ensure_yearly_file_exists(data_dir: Path, year: int) -> Path:
    """
    确保年份文件存在，如果不存在则创建
    
    Args:
        data_dir: 数据目录
        year: 年份
        
    Returns:
        Path: 年份文件路径
    """
    yearly_filename = get_yearly_filename(year)
    yearly_file = data_dir / yearly_filename
    
    if not yearly_file.exists():
        # 创建年份文件
        content = f"""; {year}年交易记录
; 自动生成的年份文件

"""
        with open(yearly_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return yearly_file


def add_include_to_main_file(main_file: Path, include_filename: str) -> bool:
    """
    将include指令添加到主文件中（如果尚未存在）
    
    Args:
        main_file: 主文件路径
        include_filename: 要包含的文件名
        
    Returns:
        bool: 是否成功添加
    """
    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经存在该include
        include_directive = f'include "{include_filename}"'
        if include_directive in content:
            return True  # 已存在，无需添加
        
        # 找到合适的位置插入include指令
        lines = content.split('\n')
        
        # 找到现有include指令的位置
        include_section_end = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('include '):
                include_section_end = i
        
        # 如果找到了include区域，在最后一个include后添加
        if include_section_end >= 0:
            lines.insert(include_section_end + 1, include_directive)
        else:
            # 如果没有include区域，在option后面添加
            option_section_end = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('option '):
                    option_section_end = i
            
            if option_section_end >= 0:
                # 在option区域后添加
                lines.insert(option_section_end + 1, '')
                lines.insert(option_section_end + 2, '; 年份文件引用')
                lines.insert(option_section_end + 3, include_directive)
            else:
                # 在文件开头添加
                lines.insert(0, include_directive)
                lines.insert(1, '')
        
        # 写回文件
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return True
        
    except Exception:
        return False


def get_existing_yearly_files(data_dir: Path) -> List[int]:
    """
    获取已存在的年份文件列表
    
    Args:
        data_dir: 数据目录
        
    Returns:
        List[int]: 年份列表，按年份排序
    """
    yearly_files = []
    pattern = r"transactions_(\d{4})\.beancount"
    
    for file_path in data_dir.glob("transactions_*.beancount"):
        match = re.match(pattern, file_path.name)
        if match:
            year = int(match.group(1))
            yearly_files.append(year)
    
    return sorted(yearly_files)


def append_transaction_to_yearly_file(yearly_file: Path, transaction_content: str) -> bool:
    """
    将交易内容追加到年份文件中
    
    Args:
        yearly_file: 年份文件路径
        transaction_content: 交易内容
        
    Returns:
        bool: 是否成功追加
    """
    try:
        with open(yearly_file, 'a', encoding='utf-8') as f:
            f.write('\n' + transaction_content + '\n')
        return True
    except Exception:
        return False 