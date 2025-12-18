"""
时间解析工具 - TimeParserTool

支持多种时间表达式的解析，将自然语言时间转换为标准日期范围。
"""
import re
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, Tuple
from calendar import monthrange

from app.ai.tools.base import Tool, ToolInput

logger = logging.getLogger(__name__)


class TimeParserTool(Tool):
    """
    时间表达式解析工具
    
    支持的时间表达式:
    1. 相对时间: 上个月、今年、去年、上周、最近N天
    2. 绝对月份: 8月、2024年8月  
    3. 日期范围: 8.5到9.12、8月5日到9月12日、2024-08-05至2024-09-12
    4. 季度表达: Q1、第一季度、上季度
    """
    
    @property
    def name(self) -> str:
        return "time_parser_tool"
    
    @property
    def description(self) -> str:
        return "时间表达式解析工具，将自然语言时间转换为标准日期范围"
    
    def execute(self, tool_input: ToolInput) -> Dict[str, Any]:
        """
        执行时间解析
        
        Args:
            tool_input: 包含 time_expression 参数
            
        Returns:
            {
                "success": True/False,
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD", 
                "period_desc": "时间段描述"
            }
        """
        time_expression = tool_input.get_data("time_expression", "")
        
        if not time_expression:
            return {
                "success": False,
                "error": "时间表达式不能为空"
            }
        
        try:
            result = self._parse_time_expression(time_expression)
            
            if result is None:
                return {
                    "success": False,
                    "error": f"无法解析时间表达式: {time_expression}"
                }
            
            start_date, end_date = result
            period_desc = self._format_period_description(start_date, end_date)
            
            logger.info(f"[TimeParser] 解析成功: '{time_expression}' -> {start_date.date()} ~ {end_date.date()}")
            
            return {
                "success": True,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "period_desc": period_desc
            }
            
        except Exception as e:
            logger.error(f"[TimeParser] 解析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_time_expression(self, text: str) -> Optional[Tuple[datetime, datetime]]:
        """
        解析时间表达式，返回 (start_date, end_date) 元组
        
        优先级顺序：
        1. 日期范围（最具体）
        2. 带年月份
        3. 季度
        4. 相对时间
        5. 月份
        """
        today = datetime.now().date()
        text_lower = text.lower()
        
        # 1. 解析日期范围表达式
        date_range = self._parse_date_range(text)
        if date_range:
            return date_range
        
        # 2. YYYY年N月 格式
        year_month_match = re.search(r'(\d{4})年(\d{1,2})月', text)
        if year_month_match:
            year = int(year_month_match.group(1))
            month = int(year_month_match.group(2))
            return self._get_month_range(year, month)
        
        # 3. 季度表达
        quarter_result = self._parse_quarter(text)
        if quarter_result:
            return quarter_result
        
        # 4. 相对月份
        if re.search(r'上上个?月|前两个月', text_lower):
            last_month = today.replace(day=1) - timedelta(days=1)
            two_months_ago = last_month.replace(day=1) - timedelta(days=1)
            start = two_months_ago.replace(day=1)
            _, last_day = monthrange(two_months_ago.year, two_months_ago.month)
            end = two_months_ago.replace(day=last_day)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        if re.search(r'上个?月|前一个月', text_lower):
            last_month = today.replace(day=1) - timedelta(days=1)
            start = last_month.replace(day=1)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(last_month, datetime.max.time()))
        
        # 5. 今年/本年
        if re.search(r'今年|本年', text_lower):
            start = date(today.year, 1, 1)
            end = today
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        # 6. YYYY年 格式
        year_only_match = re.search(r'(\d{4})年(?!\d{1,2}月)', text)
        if year_only_match:
            year = int(year_only_match.group(1))
            start = date(year, 1, 1)
            end = date(year, 12, 31) if year < today.year else today
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        # 7. 去年/上一年
        if re.search(r'去年|上一?年', text_lower):
            last_year = today.year - 1
            start = date(last_year, 1, 1)
            end = date(last_year, 12, 31)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        # 8. 上周
        if re.search(r'上一?周', text_lower):
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            last_sunday = last_monday + timedelta(days=6)
            return (datetime.combine(last_monday, datetime.min.time()),
                    datetime.combine(last_sunday, datetime.max.time()))
        
        # 9. 最近/过去N天
        days_match = re.search(r'(?:最近|过去|近)(\d+)天', text_lower)
        if days_match:
            n_days = int(days_match.group(1))
            start = today - timedelta(days=n_days - 1)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(today, datetime.max.time()))
        
        # 10. N月/N月份 格式（默认当年）
        month_match = re.search(r'(\d{1,2})月份?(?!\d)', text)
        if month_match:
            month = int(month_match.group(1))
            if 1 <= month <= 12:
                year = today.year
                # 如果指定月份大于当前月份，可能指去年
                if month > today.month:
                    year = today.year - 1
                return self._get_month_range(year, month)
        
        return None
    
    def _parse_date_range(self, text: str) -> Optional[Tuple[datetime, datetime]]:
        """
        解析日期范围表达式
        
        支持格式:
        - M.D-M.D: 8.5-9.12, 8.5到9.12
        - M月D日到M月D日: 8月5日到9月12日
        - YYYY-MM-DD至YYYY-MM-DD: 2024-08-05至2024-09-12
        - YYYY.M.D-YYYY.M.D: 2024.8.5-2024.9.12
        """
        today = datetime.now().date()
        
        # 1. 标准格式: YYYY-MM-DD 至 YYYY-MM-DD
        pattern1 = r'(\d{4})-(\d{1,2})-(\d{1,2})[-~到至](\d{4})-(\d{1,2})-(\d{1,2})'
        match1 = re.search(pattern1, text)
        if match1:
            start = date(int(match1.group(1)), int(match1.group(2)), int(match1.group(3)))
            end = date(int(match1.group(4)), int(match1.group(5)), int(match1.group(6)))
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        # 2. 带年的点格式: YYYY.M.D-YYYY.M.D
        pattern2 = r'(\d{4})\.(\d{1,2})\.(\d{1,2})[-~到至](\d{4})\.(\d{1,2})\.(\d{1,2})'
        match2 = re.search(pattern2, text)
        if match2:
            start = date(int(match2.group(1)), int(match2.group(2)), int(match2.group(3)))
            end = date(int(match2.group(4)), int(match2.group(5)), int(match2.group(6)))
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        # 3. 短格式: M.D-M.D（默认当年）
        pattern3 = r'(\d{1,2})\.(\d{1,2})[-~到至](\d{1,2})\.(\d{1,2})'
        match3 = re.search(pattern3, text)
        if match3:
            start_month, start_day = int(match3.group(1)), int(match3.group(2))
            end_month, end_day = int(match3.group(3)), int(match3.group(4))
            
            # 推断年份
            start_year = today.year
            end_year = today.year
            
            # 如果结束月份小于开始月份，可能跨年
            if end_month < start_month:
                end_year = today.year + 1
            
            start = date(start_year, start_month, start_day)
            end = date(end_year, end_month, end_day)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        # 4. 中文格式: M月D日到M月D日
        pattern4 = r'(\d{1,2})月(\d{1,2})日[-~到至](\d{1,2})月(\d{1,2})日'
        match4 = re.search(pattern4, text)
        if match4:
            start_month, start_day = int(match4.group(1)), int(match4.group(2))
            end_month, end_day = int(match4.group(3)), int(match4.group(4))
            
            start_year = today.year
            end_year = today.year
            
            if end_month < start_month:
                end_year = today.year + 1
            
            start = date(start_year, start_month, start_day)
            end = date(end_year, end_month, end_day)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        # 5. 混合格式: YYYY年M月D日至M月D日
        pattern5 = r'(\d{4})年(\d{1,2})月(\d{1,2})日[-~到至](\d{1,2})月(\d{1,2})日'
        match5 = re.search(pattern5, text)
        if match5:
            start_year = int(match5.group(1))
            start_month, start_day = int(match5.group(2)), int(match5.group(3))
            end_month, end_day = int(match5.group(4)), int(match5.group(5))
            
            end_year = start_year
            if end_month < start_month:
                end_year = start_year + 1
            
            start = date(start_year, start_month, start_day)
            end = date(end_year, end_month, end_day)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        return None
    
    def _parse_quarter(self, text: str) -> Optional[Tuple[datetime, datetime]]:
        """
        解析季度表达式
        
        支持:
        - Q1/Q2/Q3/Q4
        - 第一季度/第二季度/第三季度/第四季度
        - 上季度/本季度
        """
        today = datetime.now().date()
        current_month = today.month
        current_quarter = (current_month - 1) // 3 + 1
        
        quarter_map = {
            1: (1, 3),   # Q1: 1-3月
            2: (4, 6),   # Q2: 4-6月
            3: (7, 9),   # Q3: 7-9月
            4: (10, 12)  # Q4: 10-12月
        }
        
        # Q1/Q2/Q3/Q4
        q_match = re.search(r'Q([1-4])', text, re.IGNORECASE)
        if q_match:
            quarter = int(q_match.group(1))
            start_month, end_month = quarter_map[quarter]
            start = date(today.year, start_month, 1)
            _, last_day = monthrange(today.year, end_month)
            end = date(today.year, end_month, last_day)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        # 第N季度
        quarter_cn_match = re.search(r'第([一二三四1-4])季度', text)
        if quarter_cn_match:
            quarter_str = quarter_cn_match.group(1)
            quarter_cn_map = {'一': 1, '二': 2, '三': 3, '四': 4}
            quarter = quarter_cn_map.get(quarter_str, int(quarter_str))
            start_month, end_month = quarter_map[quarter]
            start = date(today.year, start_month, 1)
            _, last_day = monthrange(today.year, end_month)
            end = date(today.year, end_month, last_day)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        # 上季度
        if re.search(r'上季度', text):
            last_quarter = current_quarter - 1 if current_quarter > 1 else 4
            year = today.year if current_quarter > 1 else today.year - 1
            start_month, end_month = quarter_map[last_quarter]
            start = date(year, start_month, 1)
            _, last_day = monthrange(year, end_month)
            end = date(year, end_month, last_day)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        # 本季度
        if re.search(r'本季度', text):
            start_month, end_month = quarter_map[current_quarter]
            start = date(today.year, start_month, 1)
            # 本季度截止到今天
            if end_month >= current_month:
                end = today
            else:
                _, last_day = monthrange(today.year, end_month)
                end = date(today.year, end_month, last_day)
            return (datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()))
        
        return None
    
    def _get_month_range(self, year: int, month: int) -> Tuple[datetime, datetime]:
        """获取指定年月的日期范围"""
        start = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end = date(year, month, last_day)
        return (datetime.combine(start, datetime.min.time()),
                datetime.combine(end, datetime.max.time()))
    
    def _format_period_description(self, start: datetime, end: datetime) -> str:
        """格式化时间段描述"""
        start_date = start.date()
        end_date = end.date()
        
        # 如果是整月
        if start_date.day == 1:
            _, last_day = monthrange(start_date.year, start_date.month)
            if end_date.day == last_day and start_date.year == end_date.year and start_date.month == end_date.month:
                return f"{start_date.year}年{start_date.month}月"
        
        # 如果是整年
        if start_date.month == 1 and start_date.day == 1 and end_date.month == 12 and end_date.day == 31:
            return f"{start_date.year}年"
        
        # 通用格式
        return f"{start_date.year}年{start_date.month}月{start_date.day}日 至 {end_date.year}年{end_date.month}月{end_date.day}日"


# 工具实例
time_parser_tool = TimeParserTool()
