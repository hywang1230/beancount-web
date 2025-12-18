"""统一的日志格式化工具"""
from typing import Any


class LogFormatter:
    """Agent 日志格式化器
    
    提供统一的日志格式，用于美化 Agent 的日志输出
    """
    
    # 分隔符常量
    HEADER = "=" * 80
    DIVIDER = "-" * 40
    SUB_DIVIDER = "." * 40
    
    @staticmethod
    def section_header(title: str) -> str:
        """
        生成章节标题格式
        
        Args:
            title: 标题文本
            
        Returns:
            格式化的章节标题
            
        Example:
            >>> LogFormatter.section_header("PEER 流程开始")
            '================================================================================
            PEER 流程开始
            ================================================================================'
        """
        return f"\n{LogFormatter.HEADER}\n{title}\n{LogFormatter.HEADER}"
    
    @staticmethod
    def sub_section(title: str) -> str:
        """
        生成子章节标题格式
        
        Args:
            title: 标题文本
            
        Returns:
            格式化的子章节标题
            
        Example:
            >>> LogFormatter.sub_section("Step 1: Planning")
            '----------------------------------------
            Step 1: Planning
            ----------------------------------------'
        """
        return f"\n{LogFormatter.DIVIDER}\n{title}\n{LogFormatter.DIVIDER}"
    
    @staticmethod
    def key_value(key: str, value: Any, max_length: int = 100) -> str:
        """
        生成键值对格式的日志
        
        Args:
            key: 键名
            value: 值
            max_length: 值的最大显示长度，超过会截断
            
        Returns:
            格式化的键值对字符串
            
        Example:
            >>> LogFormatter.key_value("用户问题", "本月花了多少钱？")
            '[用户问题] 本月花了多少钱？'
        """
        value_str = str(value)
        if len(value_str) > max_length:
            value_str = value_str[:max_length] + "..."
        return f"[{key}] {value_str}"
    
    @staticmethod
    def list_item(index: int, content: str, indent: int = 0) -> str:
        """
        生成列表项格式
        
        Args:
            index: 索引号（从1开始）
            content: 内容
            indent: 缩进级别
            
        Returns:
            格式化的列表项
            
        Example:
            >>> LogFormatter.list_item(1, "分析收入情况")
            '  [1] 分析收入情况'
        """
        indent_str = "  " * indent
        return f"{indent_str}[{index}] {content}"
    
    @staticmethod
    def step(step_num: int, step_name: str, status: str = "") -> str:
        """
        生成步骤格式
        
        Args:
            step_num: 步骤编号
            step_name: 步骤名称
            status: 可选的状态信息
            
        Returns:
            格式化的步骤字符串
            
        Example:
            >>> LogFormatter.step(1, "Planning", "开始")
            '[Step 1: Planning] 开始'
        """
        step_str = f"[Step {step_num}: {step_name}]"
        if status:
            step_str += f" {status}"
        return step_str
    
    @staticmethod
    def data_summary(label: str, data: Any, preview_length: int = 500) -> str:
        """
        生成数据摘要格式
        
        Args:
            label: 数据标签
            data: 数据内容
            preview_length: 预览长度
            
        Returns:
            格式化的数据摘要
        """
        data_str = str(data)
        total_length = len(data_str)
        
        if total_length > preview_length:
            preview = data_str[:preview_length] + "..."
            return f"[{label}] 长度: {total_length} 字符\n{preview}"
        else:
            return f"[{label}] {data_str}"
