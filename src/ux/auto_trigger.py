"""
自动触发器 - 修复版

修复"喜欢"关键词触发阈值偏高的问题
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


@dataclass
class TriggerDecision:
    """触发决策结果"""
    should_save: bool
    confidence: float
    reason: str
    strategy: str


class AutoTrigger:
    """
    自动触发器 - 修复版
    
    修复内容:
    1. 关键词匹配直接使用原始内容（非lower）
    2. 提高关键词权重：单个高优先级关键词得0.9分
    3. 添加更多高优先级关键词
    """
    
    # 修复：更全面的关键词配置
    DEFAULT_KEYWORDS = {
        "high_priority": [
            # 明确指令
            "记住", "别忘了", "记下来", "保存", "记下",
            # 个人偏好（修复：单独"喜欢"而非"我喜欢"）
            "喜欢", "爱好", "偏好", "钟爱", "热爱", "最爱",
            "讨厌", "厌恶", "反感", "不喜欢", "厌烦",
            # 意愿表达
            "我要", "我想", "我希望", "我不想要", "我打算",
            # 规划类
            "计划", "目标", "梦想", "愿望", "打算", "准备",
            # 重要信息
            "重要", "关键", "核心", "必须", "一定", "务必",
            # 身份信息
            "我是", "我叫", "我的", "我们",
            # 情感表达
            "开心", "难过", "兴奋", "担心", "期待", "害怕",
            # 行为习惯
            "习惯", "经常", "总是", "从不", "通常", "一直"
        ],
        "medium_priority": [
            # 观点表达
            "觉得", "认为", "感觉", "想法", "看法", "观点",
            # 时间相关
            "明天", "下周", "下个月", "明年", "以后", "将来",
            # 程度修饰
            "非常", "特别", "很", "最", "比较", "相当",
            # 变化相关
            "改变", "变化", "变成", "改为", "换成"
        ]
    }
    
    def __init__(
        self,
        min_content_length: int = 5,  # 修复：降低最小长度
        max_content_length: int = 500,
        min_confidence: float = 0.5,  # 修复：降低阈值
        keywords: Optional[Dict[str, List[str]]] = None
    ):
        self.min_content_length = min_content_length
        self.max_content_length = max_content_length
        self.min_confidence = min_confidence
        self.keywords = keywords or self.DEFAULT_KEYWORDS.copy()
        
        self.session_history: List[Dict[str, Any]] = []
        self.last_trigger_time: Optional[datetime] = None
        self.message_count: int = 0
    
    def should_save(self, content: str, context: Optional[Dict[str, Any]] = None) -> TriggerDecision:
        """
        判断是否保存记忆 - 简化版（修复关键词触发问题）
        """
        self.message_count += 1
        
        # 基本检查
        if not content or len(content.strip()) < self.min_content_length:
            return TriggerDecision(False, 0.0, "内容太短", "length_check")
        
        # 修复：关键词检查（直接使用原始内容）
        high_matches = sum(1 for kw in self.keywords["high_priority"] if kw in content)
        medium_matches = sum(1 for kw in self.keywords["medium_priority"] if kw in content)
        
        # 修复：提高关键词权重
        if high_matches > 0:
            # 单个高优先级关键词即触发，置信度0.9
            confidence = min(1.0, 0.9 + (high_matches - 1) * 0.05)
            return TriggerDecision(
                should_save=True,
                confidence=round(confidence, 2),
                reason=f"包含{high_matches}个高优先级关键词",
                strategy="keyword_high"
            )
        
        if medium_matches >= 2:  # 修复：2个中优先级关键词触发
            confidence = min(1.0, 0.6 + (medium_matches - 2) * 0.1)
            return TriggerDecision(
                should_save=True,
                confidence=round(confidence, 2),
                reason=f"包含{medium_matches}个中优先级关键词",
                strategy="keyword_medium"
            )
        
        # 长度启发式（内容较长可能有价值）
        if len(content) > 30:
            return TriggerDecision(
                should_save=True,
                confidence=0.55,
                reason="内容较长，可能有价值",
                strategy="length_heuristic"
            )
        
        return TriggerDecision(
            should_save=False,
            confidence=0.3,
            reason="无明确保存信号",
            strategy="none"
        )
    
    def reset_session(self) -> None:
        """重置会话状态"""
        self.session_history.clear()
        self.last_trigger_time = None
        self.message_count = 0
