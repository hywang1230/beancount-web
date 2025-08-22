"""
交易验证服务
负责交易数据的验证和错误处理
"""
import os
import tempfile
from typing import Dict, List
from beancount import loader

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TransactionValidator:
    """交易验证器"""
    
    def __init__(self, main_file: str):
        self.main_file = main_file
    
    def validate_transaction(self, transaction_data: Dict) -> Dict:
        """校验交易数据但不保存到文件"""
        try:
            logger.debug(f"Validating transaction: {transaction_data.get('narration', 'Unknown')}")
            # 构建交易字符串用于验证
            transaction_str = self._build_transaction_string(transaction_data)
            
            # 使用更简单的验证策略：在主文件的目录中创建临时文件
            from app.core.config import settings
            import uuid
            
            # 生成临时文件名
            temp_filename = f"temp_validation_{uuid.uuid4().hex[:8]}.beancount"
            temp_file_path = settings.data_dir / temp_filename
            
            try:
                # 读取主文件内容，替换include指令为实际内容
                main_file_path = settings.data_dir / settings.default_beancount_file
                
                if main_file_path.exists():
                    with open(main_file_path, 'r', encoding='utf-8') as f:
                        main_content = f.read()
                    
                    # 处理include指令，替换为实际文件内容
                    temp_content = self._resolve_includes(main_content, settings.data_dir)
                    temp_content += '\n' + transaction_str + '\n'
                else:
                    # 如果主文件不存在，使用基本模板
                    temp_content = f"""
option "title" "Validation Test"
option "operating_currency" "CNY"

; 基础账户定义
1900-01-01 open Assets:Cash CNY
1900-01-01 open Assets:Bank:Checking CNY
1900-01-01 open Expenses:CY-餐饮 CNY
1900-01-01 open Liabilities:XYK-信用卡:招行:8164 CNY
1900-01-01 open Equity:Opening-Balances CNY

; 用户交易
{transaction_str}
"""
                
                # 写入临时文件
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(temp_content)
                
                # 使用beancount加载器验证临时文件
                entries, errors, options_map = loader.load_file(str(temp_file_path))
                
                # 清理临时文件
                if temp_file_path.exists():
                    temp_file_path.unlink()
                
                # 解析错误信息，提供友好的提示
                friendly_errors = []
                raw_errors = []
                if errors:
                    for error in errors[:5]:  # 最多显示5个错误
                        error_str = str(error)
                        raw_errors.append(error_str)
                        friendly_error = self._parse_validation_error(error_str)
                        friendly_errors.append(friendly_error)
                
                # 记录验证结果
                is_valid = len(errors) == 0
                if is_valid:
                    logger.debug("Transaction validation successful")
                else:
                    logger.warning(f"Transaction validation failed with {len(errors)} errors")
                    for error in friendly_errors:
                        logger.warning(f"Validation error: {error}")
                
                # 返回验证结果
                return {
                    "valid": is_valid,
                    "entries_count": len(entries),
                    "errors_count": len(errors),
                    "errors": friendly_errors,
                    "raw_errors": raw_errors,  # 保留原始错误信息供调试使用
                    "transaction_str": transaction_str
                }
                
            except Exception as e:
                # 清理临时文件
                if temp_file_path.exists():
                    temp_file_path.unlink()
                raise e
                
        except Exception as e:
            logger.error(f"Transaction validation exception: {e}")
            return {
                "valid": False,
                "errors_count": 1,
                "errors": [f"交易校验失败: {str(e)}"],
                "transaction_str": ""
            }
    
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
    
    def _parse_validation_error(self, error_str: str) -> str:
        """解析验证错误并返回用户友好的信息"""
        try:
            # 提取错误消息
            if "message=" in error_str:
                # 查找 message= 后面的内容
                message_start = error_str.find("message=") + 8
                message_part = error_str[message_start:]
                
                # 如果消息被引号包围，提取引号内的内容
                if message_part.startswith('"'):
                    message_end = message_part.find('"', 1)
                    if message_end > 0:
                        message = message_part[1:message_end]
                    else:
                        message = message_part
                else:
                    # 查找到下一个字段或结束
                    message_end = message_part.find("', entry=")
                    if message_end > 0:
                        message = message_part[:message_end]
                    else:
                        message = message_part
                
                # 处理常见的错误类型并提供友好提示
                if "Invalid currency" in message:
                    # 从错误信息中提取货币和账户
                    if "for account" in message:
                        parts = message.split("for account")
                        if len(parts) >= 2:
                            currency_part = parts[0].replace("Invalid currency", "").strip()
                            account_part = parts[1].replace("'", "").strip()
                            return f"账户 {account_part} 不支持货币 {currency_part}，请检查账户的货币限制"
                    return f"货币类型错误：{message}"
                
                elif "Invalid reference to unknown account" in message:
                    # 提取账户名
                    account = message.replace("Invalid reference to unknown account", "").replace("'", "").strip()
                    return f"账户 '{account}' 不存在，请先创建该账户或选择其他账户"
                
                elif "Invalid reference to inactive account" in message:
                    # 提取账户名
                    account = message.replace("Invalid reference to inactive account", "").replace("'", "").strip()
                    return f"账户 '{account}' 已关闭，无法使用该账户进行交易"
                
                elif "Transaction does not balance" in message:
                    # 提取差额
                    balance_part = message.replace("Transaction does not balance:", "").strip()
                    return f"交易不平衡，差额为 {balance_part}，请检查各分录金额"
                
                elif "Invalid account name" in message:
                    # 提取账户名
                    account = message.replace("Invalid account name:", "").replace("'", "").strip()
                    return f"账户名称 '{account}' 格式不正确，请使用英文和冒号分隔的格式"
                
                else:
                    # 返回原始消息（去掉多余字符）
                    return message.replace('\\', '').replace('"', '')
            
            # 如果无法解析，返回简化的错误信息
            if "ValidationError" in error_str:
                return "数据校验失败，请检查输入内容"
            elif "ParserError" in error_str:
                return "数据格式错误，请检查输入格式"
            else:
                return "未知错误，请检查输入内容"
                
        except Exception:
            return "数据校验失败，请检查输入内容"
    
    def _resolve_includes(self, content: str, base_dir) -> str:
        """
        解析并替换include指令为实际文件内容
        
        Args:
            content: 主文件内容
            base_dir: 文件基础目录
            
        Returns:
            str: 解析后的内容
        """
        from pathlib import Path
        lines = content.split('\n')
        resolved_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('include '):
                # 解析include指令
                import re
                match = re.match(r'include\s+["\']([^"\']+)["\']', stripped_line)
                if match:
                    include_filename = match.group(1)
                    include_path = base_dir / include_filename
                    
                    if include_path.exists():
                        try:
                            with open(include_path, 'r', encoding='utf-8') as f:
                                include_content = f.read()
                            resolved_lines.append(f'; Contents from {include_filename}')
                            resolved_lines.append(include_content)
                        except Exception as e:
                            logger.warning(f"Failed to read include file {include_filename}: {e}")
                            resolved_lines.append(f'; Error reading {include_filename}')
                    else:
                        logger.warning(f"Include file not found: {include_filename}")
                        resolved_lines.append(f'; Include file not found: {include_filename}')
                else:
                    resolved_lines.append(line)
            else:
                resolved_lines.append(line)
        
        return '\n'.join(resolved_lines)
