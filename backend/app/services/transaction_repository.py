"""
交易仓储服务
负责交易的增删改查操作
"""
import os
import re
from typing import Dict, Optional
from datetime import date
from beancount.core.data import Transaction


class TransactionRepository:
    """交易仓储"""
    
    def __init__(self, main_file: str, loader):
        self.main_file = main_file
        self.loader = loader
        # 导入年份文件管理器
        from app.services.yearly_file_manager import yearly_file_manager
        self.yearly_file_manager = yearly_file_manager
    
    def add_transaction(self, transaction_data: Dict) -> bool:
        """添加新交易到账本文件"""
        try:
            # 构建交易字符串
            transaction_str = self._build_transaction_string(transaction_data)
            
            # 解析交易日期
            transaction_date = date.fromisoformat(transaction_data['date'])
            
            # 使用年份文件管理器将交易写入对应年份文件
            success = self.yearly_file_manager.add_transaction_to_yearly_file(
                transaction_date, transaction_str
            )
            
            if success:
                # 重新加载条目
                self.loader.load_entries(force_reload=True)
                return True
            else:
                return False
            
        except Exception as e:
            # Transaction addition failed
            return False
    
    def update_transaction_by_location(self, filename: str, lineno: int, transaction_data: Dict) -> bool:
        """根据文件名和行号更新交易"""
        try:
            # 首先找到要更新的交易
            entries, _, _ = self.loader.load_entries()
            target_entry = None
            
            for entry in entries:
                if isinstance(entry, Transaction):
                    entry_filename = entry.meta.get('filename') if entry.meta else None
                    entry_lineno = entry.meta.get('lineno') if entry.meta else None
                    
                    if entry_filename and entry_lineno:
                        entry_basename = os.path.basename(entry_filename)
                        if entry_basename == filename and entry_lineno == lineno:
                            target_entry = entry
                            break
            
            if not target_entry:
                return False
            
            # 读取原始文件内容
            target_filename = target_entry.meta.get('filename')
            if not target_filename:
                return False
            
            with open(target_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 构建新的交易字符串
            new_transaction_str = self._build_transaction_string(transaction_data)
            
            # 找到交易的起始行和结束行
            start_line, end_line = self._find_transaction_range(lines, lineno)
            
            # 替换整个交易块
            if start_line < len(lines):
                # 删除原有的交易行
                del lines[start_line:end_line + 1]
                
                # 在原位置插入新的交易内容
                new_lines = (new_transaction_str + '\n').split('\n')
                # 移除最后一个空行（split产生的）
                if new_lines and not new_lines[-1]:
                    new_lines = new_lines[:-1]
                
                for i, new_line in enumerate(new_lines):
                    lines.insert(start_line + i, new_line + '\n')
                
                # 写回文件
                with open(target_filename, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                # 重新加载条目
                self.loader.load_entries(force_reload=True)
                return True
            
            return False
            
        except Exception as e:
            return False
    
    def delete_transaction_by_location(self, filename: str, lineno: int) -> bool:
        """根据文件名和行号删除交易"""
        try:
            # 首先找到要删除的交易
            entries, _, _ = self.loader.load_entries()
            target_entry = None
            
            for entry in entries:
                if isinstance(entry, Transaction):
                    entry_filename = entry.meta.get('filename') if entry.meta else None
                    entry_lineno = entry.meta.get('lineno') if entry.meta else None
                    
                    if entry_filename and entry_lineno:
                        entry_basename = os.path.basename(entry_filename)
                        if entry_basename == filename and entry_lineno == lineno:
                            target_entry = entry
                            break
            
            if not target_entry:
                return False
            
            # 读取原始文件内容
            target_filename = target_entry.meta.get('filename')
            if not target_filename:
                return False
            
            with open(target_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 找到交易的起始行和结束行
            start_line, end_line = self._find_transaction_range(lines, lineno)
            
            # 直接删除整个交易块
            if start_line < len(lines):
                # 删除交易的所有行
                del lines[start_line:end_line + 1]
                
                # 写回文件
                with open(target_filename, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                # 重新加载条目
                self.loader.load_entries(force_reload=True)
                return True
            
            return False
            
        except Exception as e:
            return False
    
    def _find_transaction_range(self, lines: list, lineno: int) -> tuple:
        """找到交易的起始行和结束行"""
        start_line = lineno - 1  # 转换为0基索引
        end_line = start_line
        
        # 查找交易的结束行：从起始行开始，找到下一个不以空格或制表符开头的行
        for i in range(start_line + 1, len(lines)):
            line = lines[i].rstrip()
            if line and not line.startswith(('  ', '\t')) and not line.startswith(';'):
                # 找到下一个交易或其他条目的开始
                end_line = i - 1
                break
            elif i == len(lines) - 1:
                # 这是文件的最后一行
                end_line = i
                break
            elif line.strip():
                # 这是交易的一部分（posting行）
                end_line = i
        
        return start_line, end_line
    
    def _build_transaction_string(self, data: Dict) -> str:
        """构建交易字符串"""
        lines = []
        
        # 交易头部
        date_str = data['date']
        flag = data.get('flag', '*')
        payee = f'"{data["payee"]}"' if data.get('payee') else ''
        narration = f'"{data["narration"]}"'
        
        header = f"{date_str} {flag} {payee} {narration}".strip()
        lines.append(header)
        
        # 添加分录
        for posting in data['postings']:
            account = posting['account']
            
            if posting.get('amount') and posting.get('currency'):
                amount_str = f"  {account}  {posting['amount']} {posting['currency']}"
            else:
                amount_str = f"  {account}"
            
            lines.append(amount_str)
        
        return '\n'.join(lines)
