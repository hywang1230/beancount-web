"""
年份文件管理服务
负责按年份自动分文件管理交易记录
"""
from pathlib import Path
from datetime import date
from typing import List, Optional, Tuple
import re

from app.core.config import settings
from app.core.logging_config import get_logger
from app.utils.file_utils import (
    get_yearly_filename,
    ensure_yearly_file_exists,
    add_include_to_main_file,
    get_existing_yearly_files,
    append_transaction_to_yearly_file
)

logger = get_logger(__name__)


class YearlyFileManager:
    """年份文件管理器"""
    
    def __init__(self):
        self.data_dir = settings.data_dir
        self.main_file = self.data_dir / settings.default_beancount_file
    
    def get_yearly_file_for_date(self, transaction_date: date) -> Path:
        """
        根据交易日期获取对应的年份文件
        
        Args:
            transaction_date: 交易日期
            
        Returns:
            Path: 年份文件路径
        """
        year = transaction_date.year
        return self.ensure_yearly_file_exists(year)
    
    def ensure_yearly_file_exists(self, year: int) -> Path:
        """
        确保年份文件存在，并在主文件中添加引用
        
        Args:
            year: 年份
            
        Returns:
            Path: 年份文件路径
        """
        yearly_file = ensure_yearly_file_exists(self.data_dir, year)
        yearly_filename = get_yearly_filename(year)
        
        # 在主文件中添加引用
        success = add_include_to_main_file(self.main_file, yearly_filename)
        if not success:
            logger.warning(f"Failed to add include for {yearly_filename} to main file")
        else:
            logger.info(f"Ensured yearly file {yearly_filename} exists and is included")
        
        return yearly_file
    
    def add_transaction_to_yearly_file(self, transaction_date: date, transaction_content: str) -> bool:
        """
        将交易添加到对应年份的文件中
        
        Args:
            transaction_date: 交易日期
            transaction_content: 交易内容（Beancount格式）
            
        Returns:
            bool: 是否成功添加
        """
        try:
            yearly_file = self.get_yearly_file_for_date(transaction_date)
            success = append_transaction_to_yearly_file(yearly_file, transaction_content)
            
            if success:
                logger.info(f"Successfully added transaction to {yearly_file.name}")
                
                # 验证添加后的完整账本是否仍然有效
                self._validate_complete_ledger()
            else:
                logger.error(f"Failed to add transaction to {yearly_file.name}")
            
            return success
        except Exception as e:
            logger.error(f"Error adding transaction to yearly file: {e}")
            return False
    
    def _validate_complete_ledger(self) -> bool:
        """
        验证完整账本的有效性
        
        Returns:
            bool: 账本是否有效
        """
        try:
            from beancount import loader
            entries, errors, options_map = loader.load_file(str(self.main_file))
            
            if errors:
                logger.warning(f"Ledger validation found {len(errors)} errors")
                for error in errors[:3]:  # 只记录前3个错误
                    logger.warning(f"Ledger error: {error}")
                return False
            else:
                logger.debug("Ledger validation passed")
                return True
        except Exception as e:
            logger.error(f"Error validating complete ledger: {e}")
            return False
    
    def get_available_years(self) -> List[int]:
        """
        获取所有可用的年份文件
        
        Returns:
            List[int]: 年份列表，按年份排序
        """
        return get_existing_yearly_files(self.data_dir)
    
    def create_yearly_file_structure(self, years: List[int]) -> bool:
        """
        批量创建年份文件结构
        
        Args:
            years: 要创建的年份列表
            
        Returns:
            bool: 是否全部成功创建
        """
        try:
            success_count = 0
            for year in years:
                yearly_file = self.ensure_yearly_file_exists(year)
                if yearly_file.exists():
                    success_count += 1
            
            logger.info(f"Created {success_count}/{len(years)} yearly files")
            return success_count == len(years)
        except Exception as e:
            logger.error(f"Error creating yearly file structure: {e}")
            return False
    
    def migrate_transactions_by_year(self, source_file: Optional[Path] = None) -> bool:
        """
        将现有交易按年份迁移到对应的年份文件中，并从原文件删除已迁移的交易
        
        Args:
            source_file: 源文件路径，默认为主文件
            
        Returns:
            bool: 是否成功迁移
        """
        if source_file is None:
            source_file = self.main_file
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析交易条目和剩余内容
            transactions_by_year, remaining_content = self._parse_and_extract_transactions(content)
            
            if not transactions_by_year:
                logger.info("No transactions found to migrate")
                return True
            
            # 将交易迁移到对应年份文件
            migration_success = True
            for year, transactions in transactions_by_year.items():
                yearly_file = self.ensure_yearly_file_exists(year)
                
                for transaction in transactions:
                    if not append_transaction_to_yearly_file(yearly_file, transaction):
                        logger.error(f"Failed to append transaction to {yearly_file.name}")
                        migration_success = False
            
            # 只有在所有交易都成功迁移后，才更新原文件
            if migration_success:
                with open(source_file, 'w', encoding='utf-8') as f:
                    f.write(remaining_content)
                
                migrated_count = sum(len(transactions) for transactions in transactions_by_year.values())
                logger.info(f"Successfully migrated {migrated_count} transactions from {source_file.name} to yearly files")
                return True
            else:
                logger.error("Migration failed, original file unchanged")
                return False
            
        except Exception as e:
            logger.error(f"Error migrating transactions by year: {e}")
            return False
    
    def _parse_and_extract_transactions(self, content: str) -> tuple:
        """
        解析内容中的交易并按年份分组，同时返回移除交易后的剩余内容
        
        Args:
            content: 文件内容
            
        Returns:
            tuple: (transactions_by_year, remaining_content)
        """
        transactions_by_year = {}
        transaction_ranges = []  # 记录交易在文件中的位置
        
        # 改进的正则表达式匹配交易条目
        # 匹配完整的交易，包括所有posting行，但排除open/close等指令
        transaction_pattern = r'(\d{4}-\d{2}-\d{2})\s+[\*!]\s+.*?(?=\n\d{4}-\d{2}-\d{2}(?:\s+[\*!]|\s+open|\s+close|\s+balance)|\n[a-zA-Z]|\n\n|\Z)'
        
        matches = list(re.finditer(transaction_pattern, content, re.DOTALL))
        
        for match in matches:
            transaction_text = match.group(0).strip()
            date_str = match.group(1)
            
            try:
                transaction_date = date.fromisoformat(date_str)
                year = transaction_date.year
                
                if year not in transactions_by_year:
                    transactions_by_year[year] = []
                
                transactions_by_year[year].append(transaction_text)
                
                # 记录这个交易在文件中的位置
                transaction_ranges.append((match.start(), match.end()))
                
            except ValueError:
                # 跳过无效日期
                continue
        
        # 构建剩余内容（移除所有匹配的交易）
        remaining_content = self._remove_transactions_from_content(content, transaction_ranges)
        
        return transactions_by_year, remaining_content
    
    def _remove_transactions_from_content(self, content: str, transaction_ranges: List[tuple]) -> str:
        """
        从内容中移除指定范围的交易
        
        Args:
            content: 原始内容
            transaction_ranges: 交易在内容中的位置范围列表 [(start, end), ...]
            
        Returns:
            str: 移除交易后的内容
        """
        if not transaction_ranges:
            return content
        
        # 按位置倒序排序，从后往前删除，避免位置偏移
        transaction_ranges.sort(key=lambda x: x[0], reverse=True)
        
        remaining_content = content
        for start, end in transaction_ranges:
            # 移除交易及其前后的空行
            before_part = remaining_content[:start].rstrip()
            after_part = remaining_content[end:].lstrip()
            
            # 如果前面有内容且后面也有内容，保留一个空行作为分隔
            if before_part and after_part:
                remaining_content = before_part + '\n\n' + after_part
            else:
                remaining_content = before_part + after_part
        
        return remaining_content
    
    def _parse_transactions_by_year(self, content: str) -> dict:
        """
        解析内容中的交易并按年份分组（保留向后兼容）
        
        Args:
            content: 文件内容
            
        Returns:
            dict: {年份: [交易列表]}
        """
        transactions_by_year, _ = self._parse_and_extract_transactions(content)
        return transactions_by_year
    
    def cleanup_empty_yearly_files(self) -> int:
        """
        清理空的年份文件
        
        Returns:
            int: 清理的文件数量
        """
        cleaned_count = 0
        yearly_files = self.get_available_years()
        
        for year in yearly_files:
            yearly_filename = get_yearly_filename(year)
            yearly_file = self.data_dir / yearly_filename
            
            try:
                with open(yearly_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # 检查文件是否只包含注释或为空
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                non_comment_lines = [line for line in lines if not line.startswith(';')]
                
                if not non_comment_lines:
                    # 文件为空或只有注释，可以删除
                    yearly_file.unlink()
                    cleaned_count += 1
                    logger.info(f"Cleaned up empty yearly file: {yearly_filename}")
                    
            except Exception as e:
                logger.error(f"Error checking yearly file {yearly_filename}: {e}")
        
        return cleaned_count


# 创建全局实例
yearly_file_manager = YearlyFileManager()
