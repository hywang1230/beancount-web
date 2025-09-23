"""
账本选项和价格管理服务
负责直接编辑账本文件中的 operating_currency 和 Price 指令
"""
import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from datetime import date
from decimal import Decimal
import logging

from app.core.config import settings
from app.models.schemas import PriceEntry, PriceFilter
from app.services.ledger_loader import LedgerLoader

logger = logging.getLogger(__name__)


class LedgerOptionsService:
    """账本选项和价格管理服务"""
    
    def __init__(self, ledger_loader: LedgerLoader):
        self.data_dir = settings.data_dir
        self.main_file = self.data_dir / settings.default_beancount_file
        self.ledger_loader = ledger_loader
    
    def get_operating_currency(self) -> str:
        """获取当前主币种"""
        try:
            _, _, options_map = self.ledger_loader.load_entries()
            return options_map.get('operating_currency', ['CNY'])[0]
        except Exception as e:
            logger.error(f"获取主币种失败: {e}")
            return 'CNY'  # 默认值
    
    def update_operating_currency(self, new_currency: str) -> bool:
        """更新主币种"""
        try:
            # 验证货币代码格式
            if not self._validate_currency_code(new_currency):
                raise ValueError(f"无效的货币代码: {new_currency}")
            
            # 读取主文件内容
            if not self.main_file.exists():
                raise FileNotFoundError(f"主文件不存在: {self.main_file}")
            
            with open(self.main_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找并更新 operating_currency 行
            updated = False
            operating_currency_pattern = re.compile(r'^option\s+"operating_currency"\s+"([^"]+)"')
            
            for i, line in enumerate(lines):
                match = operating_currency_pattern.match(line.strip())
                if match:
                    lines[i] = f'option "operating_currency" "{new_currency}"\n'
                    updated = True
                    break
            
            # 如果没有找到，在文件开头添加
            if not updated:
                # 找到合适的位置插入（在其他 option 之后，在 include 之前）
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('option '):
                        insert_pos = i + 1
                    elif line.strip().startswith('include ') and insert_pos == 0:
                        insert_pos = i
                        break
                
                lines.insert(insert_pos, f'option "operating_currency" "{new_currency}"\n')
            
            # 写回文件
            with open(self.main_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # 重新加载账本
            self.ledger_loader.load_entries(force_reload=True)
            
            logger.info(f"成功更新主币种为: {new_currency}")
            return True
            
        except Exception as e:
            logger.error(f"更新主币种失败: {e}")
            return False
    
    def get_prices(self, filter_params: Optional[PriceFilter] = None, 
                   page: int = 1, page_size: int = 50) -> Tuple[List[PriceEntry], int]:
        """获取价格列表"""
        try:
            # 读取所有包含文件，查找 Price 指令
            prices = self._extract_prices_from_files()
            
            # 应用筛选
            if filter_params:
                prices = self._filter_prices(prices, filter_params)
            
            # 按日期倒序排序
            prices.sort(key=lambda x: x.entry_date, reverse=True)
            
            # 分页
            total = len(prices)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_prices = prices[start:end]
            
            return paginated_prices, total
            
        except Exception as e:
            logger.error(f"获取价格列表失败: {e}")
            return [], 0
    
    def add_price(self, date_: date, from_currency: str, 
                  to_currency: Optional[str] = None, rate: Decimal = None) -> bool:
        """添加或更新价格"""
        try:
            # 验证参数
            if not self._validate_currency_code(from_currency):
                raise ValueError(f"无效的源货币代码: {from_currency}")
            
            if to_currency is None:
                to_currency = self.get_operating_currency()
            
            if not self._validate_currency_code(to_currency):
                raise ValueError(f"无效的目标货币代码: {to_currency}")
            
            if rate <= 0:
                raise ValueError("汇率必须大于0")
            
            # 禁止主币→主币且汇率不为1
            if from_currency == to_currency and rate != 1:
                raise ValueError("同一货币的汇率必须为1")
            
            # 格式化价格行
            price_line = f'{date_} price {from_currency} {rate:.4f} {to_currency}\n'
            
            # 查找合适的文件添加价格
            target_file = self._find_or_create_price_file(date_.year)
            
            # 读取文件内容
            with open(target_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找是否已存在同日期同货币对的价格
            existing_line_index = self._find_existing_price_line(
                lines, date_, from_currency, to_currency
            )
            
            if existing_line_index is not None:
                # 替换现有行
                lines[existing_line_index] = price_line
                logger.info(f"更新价格: {date_} {from_currency} -> {to_currency}")
            else:
                # 找到合适位置插入（按日期排序）
                insert_pos = self._find_price_insert_position(lines, date_)
                lines.insert(insert_pos, price_line)
                logger.info(f"添加价格: {date_} {from_currency} -> {to_currency}")
            
            # 写回文件
            with open(target_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # 重新加载账本
            self.ledger_loader.load_entries(force_reload=True)
            
            return True
            
        except Exception as e:
            logger.error(f"添加价格失败: {e}")
            return False
    
    def delete_price(self, date_: date, from_currency: str, 
                     to_currency: Optional[str] = None) -> bool:
        """删除价格"""
        try:
            if to_currency is None:
                to_currency = self.get_operating_currency()
            
            # 查找包含该价格的文件
            files_to_check = self._get_price_files()
            
            for file_path in files_to_check:
                if self._delete_price_from_file(file_path, date_, from_currency, to_currency):
                    # 重新加载账本
                    self.ledger_loader.load_entries(force_reload=True)
                    logger.info(f"删除价格: {date_} {from_currency} -> {to_currency}")
                    return True
            
            logger.warning(f"未找到价格: {date_} {from_currency} -> {to_currency}")
            return False
            
        except Exception as e:
            logger.error(f"删除价格失败: {e}")
            return False
    
    def get_effective_rate(self, date_: date, from_currency: str, 
                          to_currency: Optional[str] = None) -> Optional[Decimal]:
        """获取指定日期的有效汇率（当日及之前最近的价格）"""
        try:
            if to_currency is None:
                to_currency = self.get_operating_currency()
            
            if from_currency == to_currency:
                return Decimal('1')
            
            # 获取所有价格
            all_prices, _ = self.get_prices()
            
            # 筛选匹配的货币对，且日期 <= 指定日期
            matching_prices = [
                p for p in all_prices
                if p.from_currency == from_currency 
                and p.to_currency == to_currency 
                and p.entry_date <= date_
            ]
            
            if not matching_prices:
                return None
            
            # 返回最近的价格
            matching_prices.sort(key=lambda x: x.entry_date, reverse=True)
            return matching_prices[0].rate
            
        except Exception as e:
            logger.error(f"获取有效汇率失败: {e}")
            return None
    
    # 私有辅助方法
    
    def _validate_currency_code(self, currency: str) -> bool:
        """验证货币代码格式"""
        if not currency or len(currency) != 3:
            return False
        return currency.isalpha() and currency.isupper()
    
    def _extract_prices_from_files(self) -> List[PriceEntry]:
        """从所有文件中提取价格信息"""
        prices = []
        files_to_check = self._get_price_files()
        
        price_pattern = re.compile(
            r'^(\d{4}-\d{2}-\d{2})\s+price\s+([A-Z]{3})\s+([\d.]+)\s+([A-Z]{3})'
        )
        
        for file_path in files_to_check:
            if not file_path.exists():
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        match = price_pattern.match(line.strip())
                        if match:
                            date_str, from_curr, rate_str, to_curr = match.groups()
                            prices.append(PriceEntry(
                                entry_date=date.fromisoformat(date_str),
                                from_currency=from_curr,
                                to_currency=to_curr,
                                rate=Decimal(rate_str)
                            ))
            except Exception as e:
                logger.warning(f"读取价格文件失败 {file_path}: {e}")
        
        return prices
    
    def _filter_prices(self, prices: List[PriceEntry], 
                      filter_params: PriceFilter) -> List[PriceEntry]:
        """应用价格筛选条件"""
        filtered = prices
        
        if filter_params.from_currency:
            filtered = [p for p in filtered if p.from_currency == filter_params.from_currency]
        
        if filter_params.to_currency:
            filtered = [p for p in filtered if p.to_currency == filter_params.to_currency]
        
        if filter_params.price_date:
            filtered = [p for p in filtered if p.entry_date == filter_params.price_date]
        else:
            if filter_params.start_date:
                filtered = [p for p in filtered if p.entry_date >= filter_params.start_date]
            if filter_params.end_date:
                filtered = [p for p in filtered if p.entry_date <= filter_params.end_date]
        
        return filtered
    
    def _get_price_files(self) -> List[Path]:
        """获取可能包含价格信息的文件列表"""
        files = []
        
        # 主文件
        files.append(self.main_file)
        
        # 年份文件
        for year_file in self.data_dir.glob("*_*.beancount"):
            files.append(year_file)
        
        return files
    
    def _find_or_create_price_file(self, year: int) -> Path:
        """查找或创建用于存储价格的文件"""
        # 优先使用对应年份的文件
        year_file = self.data_dir / f"transactions_{year}.beancount"
        if year_file.exists():
            return year_file
        
        # 否则使用主文件
        return self.main_file
    
    def _find_existing_price_line(self, lines: List[str], date_: date, 
                                 from_currency: str, to_currency: str) -> Optional[int]:
        """查找现有的价格行索引"""
        pattern = re.compile(
            rf'^{date_}\s+price\s+{from_currency}\s+[\d.]+\s+{to_currency}'
        )
        
        for i, line in enumerate(lines):
            if pattern.match(line.strip()):
                return i
        
        return None
    
    def _find_price_insert_position(self, lines: List[str], date_: date) -> int:
        """找到价格插入的合适位置（按日期排序）"""
        price_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+price\s+')
        
        for i, line in enumerate(lines):
            match = price_pattern.match(line.strip())
            if match:
                line_date = date.fromisoformat(match.group(1))
                if date_ > line_date:
                    return i
        
        # 如果没有找到合适位置，添加到文件末尾
        return len(lines)
    
    def _delete_price_from_file(self, file_path: Path, date_: date, 
                               from_currency: str, to_currency: str) -> bool:
        """从指定文件删除价格行"""
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_index = self._find_existing_price_line(lines, date_, from_currency, to_currency)
            if line_index is not None:
                lines.pop(line_index)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                return True
            
        except Exception as e:
            logger.error(f"从文件删除价格失败 {file_path}: {e}")
        
        return False
