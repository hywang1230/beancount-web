#!/usr/bin/env python3
"""
BQL 查询功能测试脚本
用于验证 BQL 查询服务是否正常工作
"""

from app.services.ledger_loader import LedgerLoader
from app.services.bql_service import BQLService


def test_account_balances():
    """测试账户余额查询"""
    print("=" * 60)
    print("测试 1: 账户余额查询")
    print("=" * 60)
    
    loader = LedgerLoader()
    service = BQLService(loader)
    
    test_queries = [
        ("所有资产", "account sum Assets"),
        ("所有负债", "account sum Liabilities"),
        ("所有支出", "account sum Expenses"),
        ("所有收入", "account sum Income"),
        ("所有账户", "account sum"),
    ]
    
    for name, query in test_queries:
        print(f"\n查询: {name}")
        print(f"语句: {query}")
        result = service.execute_query(query)
        
        if result['success']:
            print(f"✅ 成功! 返回 {result['row_count']} 行")
            if result['rows']:
                print(f"   示例: {result['rows'][0]}")
        else:
            print(f"❌ 失败! 错误: {result['error']}")
    
    print()


def test_transaction_queries():
    """测试交易查询"""
    print("=" * 60)
    print("测试 2: 交易查询")
    print("=" * 60)
    
    loader = LedgerLoader()
    service = BQLService(loader)
    
    test_queries = [
        ("最近10笔交易", "recent transactions limit 10"),
        ("最近50笔交易", "recent transactions limit 50"),
    ]
    
    for name, query in test_queries:
        print(f"\n查询: {name}")
        print(f"语句: {query}")
        result = service.execute_query(query)
        
        if result['success']:
            print(f"✅ 成功! 返回 {result['row_count']} 行")
            if result['rows']:
                row = result['rows'][0]
                print(f"   最新交易: 日期={row[0]}, 商家={row[1]}, 描述={row[2]}")
        else:
            print(f"❌ 失败! 错误: {result['error']}")
    
    print()


def test_query_examples():
    """测试查询示例"""
    print("=" * 60)
    print("测试 3: 查询示例")
    print("=" * 60)
    
    loader = LedgerLoader()
    service = BQLService(loader)
    
    examples = service.get_query_examples()
    print(f"\n共有 {len(examples)} 个查询示例:")
    
    for i, example in enumerate(examples):
        print(f"\n{i+1}. {example['name']}")
        print(f"   描述: {example['description']}")
        print(f"   查询: {example['query']}")
    
    print()


def test_validation():
    """测试查询验证"""
    print("=" * 60)
    print("测试 4: 查询验证")
    print("=" * 60)
    
    loader = LedgerLoader()
    service = BQLService(loader)
    
    test_cases = [
        ("有效查询", "account sum Assets", True),
        ("空查询", "", False),
        ("空格查询", "   ", False),
    ]
    
    for name, query, expected_valid in test_cases:
        print(f"\n验证: {name}")
        print(f"查询: '{query}'")
        result = service.validate_query(query)
        
        if result['valid'] == expected_valid:
            print(f"✅ 验证结果符合预期: {result['valid']}")
        else:
            print(f"❌ 验证结果不符合预期!")
            print(f"   期望: {expected_valid}, 实际: {result['valid']}")
            if result.get('error'):
                print(f"   错误: {result['error']}")
    
    print()


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("BQL 查询服务测试")
    print("=" * 60 + "\n")
    
    try:
        test_account_balances()
        test_transaction_queries()
        test_query_examples()
        test_validation()
        
        print("=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

