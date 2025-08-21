"""
账户管理服务
负责账户的创建、关闭、恢复等管理操作
"""
import re
from datetime import date
from typing import List, Optional, Tuple
from beancount.core import getters
from beancount.core.data import Close


class AccountManager:
    """账户管理器"""
    
    def __init__(self, main_file: str, loader):
        self.main_file = main_file
        self.loader = loader
    
    def create_account(self, account_name: str, open_date: date, 
                      currencies: Optional[List[str]] = None, 
                      booking_method: Optional[str] = None) -> bool:
        """创建账户（添加open指令）"""
        # 验证账户名称格式
        is_valid, error_message = self._validate_account_name(account_name)
        if not is_valid:
            raise ValueError(f"无效的账户名称格式: {error_message}")
        
        # 检查账户是否已存在
        entries, _, _ = self.loader.load_entries()
        existing_accounts = getters.get_accounts(entries)
        if account_name in existing_accounts:
            raise ValueError(f"账户已存在: {account_name}")
        
        # 构建open指令字符串
        open_directive = self._build_open_directive(account_name, open_date, currencies, booking_method)
        
        # 追加到主文件
        with open(self.main_file, 'a', encoding='utf-8') as f:
            f.write('\n' + open_directive + '\n')
        
        # 重新加载条目
        self.loader.load_entries(force_reload=True)
        return True
    
    def close_account(self, account_name: str, close_date: date) -> bool:
        """归档账户（添加close指令）"""
        try:
            # 检查账户是否存在
            entries, _, _ = self.loader.load_entries()
            existing_accounts = getters.get_accounts(entries)
            if account_name not in existing_accounts:
                raise ValueError(f"账户不存在: {account_name}")
            
            # 检查账户是否已经关闭
            for entry in entries:
                if isinstance(entry, Close) and entry.account == account_name:
                    raise ValueError(f"账户已经关闭: {account_name}")
            
            # 构建close指令字符串
            close_directive = self._build_close_directive(account_name, close_date)
            
            # 追加到主文件
            with open(self.main_file, 'a', encoding='utf-8') as f:
                f.write('\n' + close_directive + '\n')
            
            # 重新加载条目
            self.loader.load_entries(force_reload=True)
            return True
            
        except Exception as e:
            # Account archiving failed
            return False
    
    def restore_account(self, account_name: str) -> bool:
        """恢复账户（删除close指令）"""
        try:
            # 检查账户是否存在且已关闭
            entries, _, _ = self.loader.load_entries()
            
            close_entry = None
            for entry in entries:
                if isinstance(entry, Close) and entry.account == account_name:
                    close_entry = entry
                    break
            
            if not close_entry:
                raise ValueError(f"账户未归档或不存在: {account_name}")
            
            # 读取主文件内容
            with open(self.main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 构建要删除的close指令（构建可能的close指令格式）
            close_date_str = close_entry.date.strftime('%Y-%m-%d')
            close_directive_patterns = [
                f"{close_date_str} close {account_name}",
                f"{close_date_str} close {account_name} ",
                f"\n{close_date_str} close {account_name}\n",
                f"\n{close_date_str} close {account_name} \n"
            ]
            
            # 尝试删除close指令
            modified = False
            for pattern in close_directive_patterns:
                if pattern in content:
                    content = content.replace(pattern, "")
                    modified = True
                    break
            
            if not modified:
                # 如果精确匹配失败，尝试使用正则表达式
                pattern = f"^{re.escape(close_date_str)} close {re.escape(account_name)}.*$"
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if not re.match(pattern, line.strip()):
                        new_lines.append(line)
                    else:
                        modified = True
                
                if modified:
                    content = '\n'.join(new_lines)
            
            if modified:
                # 写回文件
                with open(self.main_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 重新加载条目
                self.loader.load_entries(force_reload=True)
                return True
            else:
                raise ValueError(f"无法找到账户 {account_name} 的close指令")
            
        except Exception as e:
            # Account restoration failed
            raise ValueError(f"恢复账户失败: {str(e)}")
    
    def _validate_account_name(self, account_name: str) -> Tuple[bool, str]:
        """验证账户名称是否符合beancount规范"""
        # 账户名称必须符合beancount的规范
        # 1. 必须以五种账户类型之一开头
        valid_types = ['Assets', 'Liabilities', 'Equity', 'Income', 'Expenses']
        
        # 2. 由冒号分隔的多个部分组成
        parts = account_name.split(':')
        if len(parts) < 2:
            return False, "账户名称必须包含至少两个部分，用冒号分隔"
        
        # 3. 第一部分必须是有效的账户类型
        if parts[0] not in valid_types:
            return False, f"账户类型必须是以下之一: {', '.join(valid_types)}"
        
        # 4. 第二部分（实际账户名）必须以大写字母或数字开头
        second_part = parts[1]
        if not re.match(r'^[A-Z0-9]', second_part):
            return False, f"账户名称的主要部分 '{second_part}' 必须以大写字母或数字开头"
        
        # 5. 所有部分都只能包含字母、数字、汉字、下划线和连字符
        pattern = re.compile(r'^[\w\u4e00-\u9fa5-]+$')
        for i, part in enumerate(parts):
            if i == 0:  # 跳过账户类型检查
                continue
            if not pattern.match(part):
                return False, f"账户名称部分 '{part}' 包含无效字符。只能包含字母、数字、汉字、下划线和连字符"
        
        return True, ""
    
    def _build_open_directive(self, account_name: str, open_date: date, 
                             currencies: Optional[List[str]] = None, 
                             booking_method: Optional[str] = None) -> str:
        """构建open指令字符串"""
        lines = []
        
        # 日期和指令
        date_str = open_date.strftime('%Y-%m-%d')
        directive_parts = [date_str, 'open', account_name]
        
        # 添加货币约束
        if currencies:
            directive_parts.append(','.join(currencies))
        
        # 添加记账方法
        if booking_method:
            if currencies:
                directive_parts.append(f'"{booking_method}"')
            else:
                directive_parts.extend(['', f'"{booking_method}"'])
        
        lines.append(' '.join(directive_parts))
        
        return '\n'.join(lines)
    
    def _build_close_directive(self, account_name: str, close_date: date) -> str:
        """构建close指令字符串"""
        date_str = close_date.strftime('%Y-%m-%d')
        return f"{date_str} close {account_name}"
