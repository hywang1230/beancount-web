"""
AI分析服务 - 简化版实现

由于AgentUniverse框架较为复杂，这里先实现一个简化版的AI服务，
直接调用通义千问API进行财务分析，后续可以升级为完整的PEER多Agent架构。
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """处理Decimal类型的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class AIService:
    """
    AI分析服务
    
    使用通义千问API进行财务数据分析，实现PEER模式的简化版本：
    - Plan: 理解用户问题，规划分析步骤
    - Execute: 获取相关数据
    - Express: 生成分析报告
    - Review: 验证输出质量
    """
    
    def __init__(self):
        from app.core.config import settings
        self.api_key = settings.dashscope_api_key
        self.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = "qwen-plus"
        
    async def analyze(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行财务分析
        
        Args:
            query: 用户问题
            context: 可选的上下文信息
            
        Returns:
            分析结果
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "未配置DASHSCOPE_API_KEY环境变量"
            }
        
        try:
            # 1. 获取财务数据
            financial_data = await self._gather_financial_data()
            
            # 2. 构建分析提示词
            prompt = self._build_analysis_prompt(query, financial_data, context)
            
            # 3. 调用LLM进行分析
            response = await self._call_llm(prompt)
            
            return {
                "success": True,
                "query": query,
                "response": response,
                "data_summary": self._summarize_data(financial_data)
            }
            
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        多轮对话
        
        Args:
            messages: 对话历史，格式为[{"role": "user/assistant", "content": "..."}]
            
        Returns:
            回复结果
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "未配置DASHSCOPE_API_KEY环境变量"
            }
        
        try:
            # 获取财务数据作为系统上下文
            financial_data = await self._gather_financial_data()
            
            # 构建系统消息
            system_message = self._build_system_message(financial_data)
            
            # 调用LLM
            response = await self._call_llm_chat(system_message, messages)
            
            return {
                "success": True,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"AI对话失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _gather_financial_data(self) -> Dict[str, Any]:
        """收集财务数据"""
        from app.services.beancount_service import beancount_service
        from app.database import get_db
        from app.services.budget_service import BudgetService
        
        data = {}
        
        try:
            # 强制重新加载 beancount 文件，确保获取最新数据
            beancount_service.loader.load_entries(force_reload=True)
            logger.info("已强制重新加载 beancount 文件")
            
            # 获取当月损益表
            today = datetime.now().date()
            start_of_month = today.replace(day=1)
            
            income_statement = beancount_service.get_income_statement(start_of_month, today)
            data["current_month"] = {
                "total_income": float(income_statement.total_income),
                "total_expenses": float(income_statement.total_expenses),
                "net_income": float(income_statement.net_income),
                "period": f"{today.year}年{today.month}月"
            }
            
            # 获取资产负债表
            balance_sheet = beancount_service.get_balance_sheet(today)
            data["balance"] = {
                "total_assets": float(balance_sheet.total_assets),
                "total_liabilities": float(balance_sheet.total_liabilities),
                "net_worth": float(balance_sheet.net_worth)
            }
            
            # 获取最近交易明细
            from app.models.schemas import TransactionFilter
            filter_params = TransactionFilter(start_date=start_of_month, end_date=today)
            
            logger.info(f"查询日期范围: {start_of_month} 至 {today}")
            
            transactions = beancount_service.get_transactions(filter_params)
            data["recent_transactions_count"] = len(transactions)
            
            logger.info(f"获取到本月交易 {len(transactions)} 笔")
            if transactions:
                dates = [tx.date for tx in transactions]
                logger.info(f"交易日期分布: 最早 {min(dates)}, 最晚 {max(dates)}")
            
            # 保存所有交易明细供 AI 分析
            transaction_details = []
            for tx in transactions:
                tx_info = {
                    "date": tx.date.isoformat() if hasattr(tx.date, 'isoformat') else str(tx.date),
                    "payee": tx.payee or "",
                    "narration": tx.narration or "",
                }
                # 提取过账信息 - 使用正确的属性名
                postings = []
                for posting in tx.postings:
                    posting_amount = float(posting.amount) if posting.amount else 0
                    posting_currency = posting.currency or "CNY"
                    postings.append({
                        "account": posting.account,
                        "amount": posting_amount,
                        "currency": posting_currency
                    })
                tx_info["postings"] = postings
                transaction_details.append(tx_info)
            
            data["recent_transactions"] = transaction_details
            logger.info(f"已加载 {len(transaction_details)} 笔交易明细供 AI 分析")
            
            # 获取预算信息
            try:
                db = next(get_db())
                budget_service = BudgetService(db)
                budgets = budget_service.get_budgets(period_type="month")
                data["budgets_count"] = len(budgets)
                
                if budgets:
                    summary = budget_service.get_budget_summary(period_type="month")
                    data["budget_summary"] = {
                        "total_budget": float(summary.total_budget),
                        "total_spent": float(summary.total_spent),
                        "overall_progress": summary.overall_progress
                    }
            except Exception:
                data["budgets_count"] = 0
                
        except Exception as e:
            logger.warning(f"获取财务数据时出错: {e}")
            
        return data
    
    def _build_analysis_prompt(self, query: str, data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
        """构建分析提示词"""
        prompt = f"""你是一个专业的个人财务分析助手。请基于以下财务数据回答用户的问题。

## 当前财务数据

### 本月收支情况
{json.dumps(data.get('current_month', {}), ensure_ascii=False, indent=2)}

### 资产负债情况  
{json.dumps(data.get('balance', {}), ensure_ascii=False, indent=2)}

### 其他信息
- 本月交易笔数: {data.get('recent_transactions_count', 0)}
- 预算数量: {data.get('budgets_count', 0)}
"""
        
        if data.get('budget_summary'):
            prompt += f"""
### 预算执行情况
{json.dumps(data.get('budget_summary', {}), ensure_ascii=False, indent=2)}
"""
        
        prompt += f"""

## 用户问题
{query}

## 要求
1. 基于上述数据进行分析，给出专业、实用的建议
2. 如果数据不足以回答问题，请说明需要哪些额外信息
3. 回答要简洁明了，使用中文
4. 如果涉及金额，请保留2位小数
"""
        
        return prompt
    
    def _build_system_message(self, data: Dict[str, Any]) -> str:
        """构建系统消息"""
        # 构建交易明细文本
        transactions_text = ""
        recent_transactions = data.get('recent_transactions', [])
        if recent_transactions:
            transactions_text = "\n\n本月交易明细：\n"
            for tx in recent_transactions:
                date = tx.get('date', '')
                payee = tx.get('payee', '')
                narration = tx.get('narration', '')
                desc = f"{payee} {narration}".strip() or "无描述"
                postings_str = ""
                for p in tx.get('postings', []):
                    postings_str += f"  - {p['account']}: {p['amount']:.2f} {p['currency']}\n"
                transactions_text += f"- {date} {desc}\n{postings_str}"
        
        return f"""你是一个专业的个人财务分析助手，正在帮助用户分析他们的Beancount账本数据。

当前财务概况：
- 本月收入: {data.get('current_month', {}).get('total_income', 0):.2f} 元
- 本月支出: {data.get('current_month', {}).get('total_expenses', 0):.2f} 元
- 本月结余: {data.get('current_month', {}).get('net_income', 0):.2f} 元
- 总资产: {data.get('balance', {}).get('total_assets', 0):.2f} 元
- 总负债: {data.get('balance', {}).get('total_liabilities', 0):.2f} 元
- 净资产: {data.get('balance', {}).get('net_worth', 0):.2f} 元
- 本月交易笔数: {data.get('recent_transactions_count', 0)} 笔{transactions_text}

请基于以上真实数据回答用户问题，不要猜测或编造数据。回答使用中文。"""
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        request_body = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        logger.info("========== LLM 调用开始 (_call_llm) ==========")
        logger.info(f"API Base: {self.api_base}")
        logger.info(f"Model: {self.model}")
        logger.info(f"API Key (前8位): {self.api_key[:8] if self.api_key else 'None'}...")
        logger.info(f"Prompt 长度: {len(prompt)} 字符")
        logger.info(f"Prompt 内容:\n{prompt}")
        logger.debug(f"完整请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            
            logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"响应错误内容: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            answer = result["choices"][0]["message"]["content"]
            logger.info(f"响应内容长度: {len(answer)} 字符")
            logger.info(f"响应内容:\n{answer}")
            logger.info("========== LLM 调用结束 (_call_llm) ==========")
            
            return answer
    
    async def chat_stream(self, messages: List[Dict[str, str]]):
        """
        流式多轮对话
        
        Args:
            messages: 对话历史，格式为[{"role": "user/assistant", "content": "..."}]
            
        Yields:
            响应文本块
        """
        if not self.api_key:
            yield {"type": "error", "content": "未配置DASHSCOPE_API_KEY环境变量"}
            return
        
        try:
            # 获取财务数据作为系统上下文
            financial_data = await self._gather_financial_data()
            
            # 构建系统消息
            system_message = self._build_system_message(financial_data)
            
            # 流式调用LLM
            async for chunk in self._call_llm_chat_stream(system_message, messages):
                yield {"type": "content", "content": chunk}
            
            yield {"type": "done", "content": ""}
            
        except Exception as e:
            logger.error(f"AI流式对话失败: {e}")
            yield {"type": "error", "content": str(e)}

    async def _call_llm_chat_stream(self, system_message: str, messages: List[Dict[str, str]]):
        """流式调用LLM进行多轮对话"""
        all_messages = [{"role": "system", "content": system_message}]
        all_messages.extend(messages)
        
        request_body = {
            "model": self.model,
            "messages": all_messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": True  # 启用流式输出
        }
        
        logger.info("========== LLM 流式调用开始 (_call_llm_chat_stream) ==========")
        logger.info(f"API Base: {self.api_base}")
        logger.info(f"Model: {self.model}")
        logger.info(f"API Key (前8位): {self.api_key[:8] if self.api_key else 'None'}...")
        logger.info(f"消息数量: {len(all_messages)}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body
            ) as response:
                logger.info(f"响应状态码: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"响应错误内容: {error_text}")
                    raise Exception(f"API调用失败: {response.status_code}")
                
                # 处理 SSE 流
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 移除 "data: " 前缀
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        
        logger.info("========== LLM 流式调用结束 (_call_llm_chat_stream) ==========")

    async def _call_llm_chat(self, system_message: str, messages: List[Dict[str, str]]) -> str:
        """调用LLM进行多轮对话"""
        all_messages = [{"role": "system", "content": system_message}]
        all_messages.extend(messages)
        
        request_body = {
            "model": self.model,
            "messages": all_messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        logger.info("========== LLM 调用开始 (_call_llm_chat) ==========")
        logger.info(f"API Base: {self.api_base}")
        logger.info(f"Model: {self.model}")
        logger.info(f"API Key (前8位): {self.api_key[:8] if self.api_key else 'None'}...")
        logger.info(f"消息数量: {len(all_messages)}")
        logger.info(f"System Message:\n{system_message}")
        for i, msg in enumerate(messages):
            logger.info(f"Message {i+1} [{msg['role']}]: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
        logger.debug(f"完整请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            
            logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"响应错误内容: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            answer = result["choices"][0]["message"]["content"]
            logger.info(f"响应内容长度: {len(answer)} 字符")
            logger.info(f"响应内容:\n{answer}")
            logger.info("========== LLM 调用结束 (_call_llm_chat) ==========")
            
            return answer
    
    def _summarize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成数据摘要"""
        return {
            "has_income_data": bool(data.get('current_month')),
            "has_balance_data": bool(data.get('balance')),
            "has_budget_data": data.get('budgets_count', 0) > 0,
            "transactions_count": data.get('recent_transactions_count', 0)
        }


# 全局AI服务实例
ai_service = AIService()
