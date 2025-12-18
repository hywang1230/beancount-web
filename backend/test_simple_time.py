"""
简化的时间解析测试 - 直接测试核心逻辑
"""
import re
from datetime import datetime, timedelta, date
from calendar import monthrange

def parse_date_range(text: str):
    """测试日期范围解析"""
    today = datetime.now().date()
    
    # 短格式: M.D-M.D
    pattern = r'(\d{1,2})\.(\d{1,2})[-~到至](\d{1,2})\.(\d{1,2})'
    match = re.search(pattern, text)
    if match:
        start_month, start_day = int(match.group(1)), int(match.group(2))
        end_month, end_day = int(match.group(3)), int(match.group(4))
        
        start_year = today.year
        end_year = today.year
        if end_month < start_month:
            end_year = today.year + 1
        
        start = date(start_year, start_month, start_day)
        end = date(end_year, end_month, end_day)
        return (start, end)
    return None

def parse_quarter(text: str):
    """测试季度解析"""
    today = datetime.now().date()
    quarter_map = {
        1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)
    }
    
    # Q1/Q2/Q3/Q4
    q_match = re.search(r'Q([1-4])', text, re.IGNORECASE)
    if q_match:
        quarter = int(q_match.group(1))
        start_month, end_month = quarter_map[quarter]
        start = date(today.year, start_month, 1)
        _, last_day = monthrange(today.year, end_month)
        end = date(today.year, end_month, last_day)
        return (start, end)
    
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
        return (start, end)
    
    return None

def test_time_parsing():
    """测试各种时间表达式"""
    print("=" * 80)
    print("时间解析核心逻辑测试")
    print("=" * 80)
    print()
    
    test_cases = [
        ("8.5-9.12", parse_date_range),
        ("8.5到9.12", parse_date_range),
        ("Q1", parse_quarter),
        ("Q2", parse_quarter),
        ("第一季度", parse_quarter),
        ("第二季度", parse_quarter),
    ]
    
    success = 0
    total = len(test_cases)
    
    for expression, parser in test_cases:
        print(f"测试: {expression}")
        try:
            result = parser(expression)
            if result:
                start, end = result
                print(f"✓ 成功: {start} 至 {end}")
                success += 1
            else:
                print(f"✗ 失败: 无法解析")
        except Exception as e:
            print(f"✗ 异常: {e}")
        print("-" * 40)
    
    print()
    print("=" * 80)
    print(f"结果: {success}/{total} 通过 ({success*100//total}%)")
    print("=" * 80)
    
    return success == total

if __name__ == "__main__":
    import sys
    success = test_time_parsing()
    sys.exit(0 if success else 1)
