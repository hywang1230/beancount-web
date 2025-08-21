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
            
            # 创建临时验证内容
            # 获取现有文件内容
            if os.path.exists(self.main_file):
                with open(self.main_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            else:
                existing_content = ""
            
            # 拼接新交易用于验证
            temp_content = existing_content + '\n' + transaction_str + '\n'
            
            # 创建临时文件进行验证
            with tempfile.NamedTemporaryFile(mode='w', suffix='.beancount', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(temp_content)
                temp_file_path = temp_file.name
            
            try:
                # 使用beancount加载器验证临时文件
                entries, errors, options_map = loader.load_file(temp_file_path)
                
                # 清理临时文件
                os.unlink(temp_file_path)
                
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
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
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
