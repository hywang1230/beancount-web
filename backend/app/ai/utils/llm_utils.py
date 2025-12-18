"""LLM 相关的通用工具函数"""
import json
import re
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def parse_llm_json_response(response: str) -> Optional[Dict[str, Any]]:
    """
    解析 LLM 返回的 JSON 响应
    自动清理 markdown 代码块标记
    
    Args:
        response: LLM 的原始响应文本
        
    Returns:
        解析后的字典，如果解析失败返回 None
        
    Example:
        >>> response = '```json\\n{"key": "value"}\\n```'
        >>> parse_llm_json_response(response)
        {'key': 'value'}
    """
    if not response:
        return None
        
    response = response.strip()
    
    # 移除 ```json 和 ``` 标记
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    
    response = response.strip()
    
    # 尝试提取 JSON 对象
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}, 原始文本: {response[:200]}")
            return None
    
    # 如果没有找到 JSON 对象，尝试直接解析
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON 解析失败: {e}, 原始文本: {response[:200]}")
        return None


def format_currency(amount: float, currency: str = "CNY", decimals: int = 2) -> str:
    """
    格式化货币金额
    
    Args:
        amount: 金额数值
        currency: 货币代码，默认 CNY
        decimals: 小数位数，默认 2
        
    Returns:
        格式化后的货币字符串
        
    Example:
        >>> format_currency(1234.567)
        '1,234.57 CNY'
        >>> format_currency(1234.567, 'USD', 2)
        '1,234.57 USD'
    """
    formatted_amount = f"{amount:,.{decimals}f}"
    return f"{formatted_amount} {currency}"


def extract_json_from_text(text: str) -> Optional[str]:
    """
    从文本中提取 JSON 字符串
    
    Args:
        text: 包含 JSON 的文本
        
    Returns:
        提取的 JSON 字符串，如果未找到返回 None
    """
    # 尝试匹配 JSON 对象
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        return json_match.group()
    
    # 尝试匹配 JSON 数组
    array_match = re.search(r'\[[\s\S]*\]', text)
    if array_match:
        return array_match.group()
    
    return None
