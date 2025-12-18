"""
时间解析工具单元测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from app.ai.tools.time_parser_tool import time_parser_tool
from app.ai.tools.base import ToolInput


def test_time_parser():
    """测试时间解析工具的各种表达式"""
    
    test_cases = [
        # (输入, 期望的时间特征)
        ("上个月", "上月范围"),
        ("8.5-9.12", "8月5日至9月12日"),
        ("第一季度", "1月1日至3月31日"),
        ("今年", "年初至今"),
        ("2024年8月", "2024年8月"),
        ("最近30天", "30天范围"),
        ("上周", "上周一至周日"),
        ("Q2", "4月1日至6月30日"),
    ]
    
    print("=" * 80)
    print("时间解析工具测试")
    print("=" * 80)
    print()
    
    success_count = 0
    total_count = len(test_cases)
    
    for expression, expected_desc in test_cases:
        print(f"测试表达式: {expression}")
        print(f"期望结果: {expected_desc}")
        
        try:
            result = time_parser_tool.execute(ToolInput(time_expression=expression))
            
            if result.get("success"):
                start_date = result.get("start_date")
                end_date = result.get("end_date")
                period_desc = result.get("period_desc")
                
                print(f"✓ 解析成功:")
                print(f"  - 开始日期: {start_date}")
                print(f"  - 结束日期: {end_date}")
                print(f"  - 时间段: {period_desc}")
                success_count += 1
            else:
                print(f"✗ 解析失败: {result.get('error')}")
        except Exception as e:
            print(f"✗ 异常: {str(e)}")
        
        print("-" * 40)
        print()
    
    print("=" * 80)
    print(f"测试结果: {success_count}/{total_count} 通过")
    print("=" * 80)
    
    return success_count == total_count


if __name__ == "__main__":
    success = test_time_parser()
    sys.exit(0 if success else 1)
