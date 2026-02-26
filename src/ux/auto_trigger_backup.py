"""
自动触发器

智能判断何时保存记忆，无需用户手动操作。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


@dataclass
class TriggerDecision:
    """
    触发决策结果
    
    Attributes:
        should_save: 是否应该保存
        confidence: 置信度 0.0-1.0
        reason: 触发原因
        strategy: 使用的策略
    """
    should_save: bool
    confidence: float
    reason: str
    strategy: str


class AutoTrigger:
    """
    自动触发器
    
    综合分析内容、上下文、时间等因素，智能决定何时保存记忆。
    
    Attributes:
        config: 触发器配置
        session_history: 会话历史记录
        last_trigger_time: 上次触发时间
    """
    
    # 默认关键词配置
    DEFAULT_KEYWORDS = {
        "high_priority": [
            # 明确指令
            "记住", "别忘了", "记下来", "保存", "记下",
            # 个人偏好（喜好/厌恶）
            "喜欢", "爱好", "偏好", "钟爱", "热爱",
            "讨厌", "厌恶", "反感", "不喜欢",
            # 意愿表达
            "我要", "我想", "我希望", "我不想要",
            # 规划类
            "计划", "目标", "梦想", "愿望", "打算",
            # 重要信息
            "重要", "关键", "核心", "必须", "一定",
            # 身份信息
            "我是", "我叫", "我的", "我们"
        ],
        "medium_priority": [
            # 观点表达
            "觉得", "认为", "感觉", "想法", "看法",
            # 行为习惯
            "习惯", "经常", "总是", "从不", "通常",
            # 情感表达
            "开心", "难过", "兴奋", "担心", "期待",
            # 时间相关
            "明天", "下周", "下个月", "明年", "以后",
            # 程度修饰
            "非常", "特别", "很", "最", "比较"
        ]
    }
    
    def __init__(
        self,
        min_content_length: int = 10,
        max_content_length: int = 500,
        min_confidence: float = 0.6,
        keywords: Optional[Dict[str, List[str]]] = None
    ):
        """
        初始化自动触发器
        
        Args:
            min_content_length: 最小内容长度，低于此值不保存
            max_content_length: 最大内容长度，高于此值截断
            min_confidence: 最小置信度阈值，低于此值不保存
            keywords: 自定义关键词字典
        """
        self.min_content_length = min_content_length
        self.max_content_length = max_content_length
        self.min_confidence = min_confidence
        self.keywords = keywords or self.DEFAULT_KEYWORDS.copy()
        
        # 会话状态
        self.session_history: List[Dict[str, Any]] = []
        self.last_trigger_time: Optional[datetime] = None
        self.message_count: int = 0
    
    def analyze_content(self, content: str) -> Dict[str, float]:
        """
        分析内容特征
        
        Args:
            content: 要分析的内容
            
        Returns:
            Dict[str, float]: 各维度评分
        """
        scores = {
            "length_score": 0.0,
            "keyword_score": 0.0,
            "complexity_score": 0.0,
        }
        
        if not content or len(content.strip()) < self.min_content_length:
            return scores
        
        # 1. 长度评分（适中最好）
        length = len(content)
        if length < self.min_content_length:
            scores["length_score"] = 0.0
        elif length > self.max_content_length:
            scores["length_score"] = 0.5  # 过长降分
        else:
            # 线性评分：太短或太长都降分
            optimal = (self.min_content_length + self.max_content_length) / 2
            scores["length_score"] = 1.0 - abs(length - optimal) / optimal * 0.5
        
        # 2. 关键词评分（修复：直接使用原始内容匹配，提高权重）
        high_matches = sum(1 for kw in self.keywords["high_priority"] if kw in content)
        medium_matches = sum(1 for kw in self.keywords["medium_priority"] if kw in content)
        
        # 高优先级关键词权重更高（修复：单个高优先级关键词得0.8分）
        if high_matches > 0:
            keyword_score = min(1.0, 0.8 + (high_matches - 1) * 0.1)
        elif medium_matches > 0:
            keyword_score = min(1.0, medium_matches * 0.4)
        else:
            keyword_score = 0.0
        scores["keyword_score"] = keyword_score
        
        # 3. 复杂度评分（句子数、词汇多样性）
        sentences = len(re.split(r'[。！？.!?]', content))
        content_lower = content.lower()
        words = set(re.findall(r'\w+', content_lower))
        
        if sentences >= 2 and len(words) >= 10:
            scores["complexity_score"] = min(1.0, sentences * 0.1 + len(words) * 0.01)
        
        return scores
    
    def analyze_context(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        分析上下文特征
        
        Args:
            content: 当前内容
            context: 上下文信息（对话轮次、主题等）
            
        Returns:
            Dict[str, float]: 各维度评分
        """
        scores = {
            "turn_score": 0.0,
            "topic_score": 0.0,
            "intent_score": 0.0,
        }
        
        if context is None:
            context = {}
        
        # 1. 对话轮次评分（轮次越多，越可能形成完整记忆）
        turn_count = context.get("turn_count", self.message_count)
        if turn_count >= 5:
            scores["turn_score"] = min(1.0, turn_count * 0.05)
        
        # 2. 主题变化评分（主题变化时保存旧主题）
        current_topic = context.get("topic")
        last_topic = context.get("last_topic")
        if current_topic and last_topic and current_topic != last_topic:
            scores["topic_score"] = 0.8  # 主题变化，高评分
        
        # 3. 用户意图评分
        user_intent = context.get("intent", "")
        if user_intent in ["分享", "陈述", "计划"]:
            scores["intent_score"] = 0.7
        elif user_intent in ["提问", "确认"]:
            scores["intent_score"] = 0.3
        
        return scores
    
    def analyze_timing(self) -> Dict[str, float]:
        """
        分析时间特征
        
        Returns:
            Dict[str, float]: 各维度评分
        """
        scores = {
            "time_since_last": 0.0,
            "session_duration": 0.0,
        }
        
        now = datetime.now()
        
        # 1. 距离上次触发的时间
        if self.last_trigger_time:
            time_diff = (now - self.last_trigger_time).total_seconds()
            # 5分钟内不重复触发
            if time_diff < 300:
                scores["time_since_last"] = 0.0
            else:
                scores["time_since_last"] = min(1.0, time_diff / 600)
        else:
            scores["time_since_last"] = 1.0  # 首次触发
        
        # 2. 会话持续时间（消息数）
        if self.message_count >= 10:
            scores["session_duration"] = min(1.0, self.message_count * 0.02)
        
        return scores
    
    def should_save(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TriggerDecision:
        """
        综合判断是否保存记忆
        
        Args:
            content: 当前内容
            context: 上下文信息
            
        Returns:
            TriggerDecision: 触发决策结果
        """
        # 更新消息计数
        self.message_count += 1
        
        # 1. 内容分析
        content_scores = self.analyze_content(content)
        content_confidence = (
            content_scores["length_score"] * 0.3 +
            content_scores["keyword_score"] * 0.5 +
            content_scores["complexity_score"] * 0.2
        )
        
        # 2. 上下文分析
        context_scores = self.analyze_context(content, context)
        context_confidence = (
            context_scores["turn_score"] * 0.3 +
            context_scores["topic_score"] * 0.4 +
            context_scores["intent_score"] * 0.3
        )
        
        # 3. 时间分析
        timing_scores = self.analyze_timing()
        timing_confidence = (
            timing_scores["time_since_last"] * 0.6 +
            timing_scores["session_duration"] * 0.4
        )
        
        # 4. 综合评分
        total_confidence = (
            content_confidence * 0.5 +
            context_confidence * 0.3 +
            timing_confidence * 0.2
        )
        
        # 5. 决策
        if total_confidence >= self.min_confidence:
            should_save = True
            reason = self._generate_reason(
                content_scores, context_scores, timing_scores
            )
            strategy = "multi_factor"
            self.last_trigger_time = datetime.now()
        else:
            should_save = False
            reason = "置信度低于阈值"
            strategy = "none"
        
        return TriggerDecision(
            should_save=should_save,
            confidence=round(total_confidence, 3),
            reason=reason,
            strategy=strategy
        )
    
    def _generate_reason(
        self,
        content_scores: Dict[str, float],
        context_scores: Dict[str, float],
        timing_scores: Dict[str, float]
    ) -> str:
        """生成触发原因说明"""
        reasons = []
        
        if content_scores["keyword_score"] > 0.5:
            reasons.append("包含关键词")
        if content_scores["length_score"] > 0.5:
            reasons.append("内容长度适中")
        if context_scores["topic_score"] > 0.5:
            reasons.append("主题变化")
        if timing_scores["time_since_last"] > 0.5:
            reasons.append("距离上次保存已有一段时间")
        
        return "，".join(reasons) if reasons else "综合评分达标"
    
    def reset_session(self) -> None:
        """重置会话状态"""
        self.session_history.clear()
        self.last_trigger_time = None
        self.message_count = 0


if __name__ == "__main__":
    # 简单测试
    print("AutoTrigger 基础测试:\n")
    
    trigger = AutoTrigger()
    
    # 测试用例
    test_cases = [
        "你好",  # 太短，不保存
        "安哥喜欢喝咖啡，每天早上必须一杯美式咖啡",  # 关键词+长度适中
        "记住，我下周要参加一个重要会议",  # 高优先级关键词
        "今天天气不错",  # 普通内容
    ]
    
    for content in test_cases:
        decision = trigger.should_save(content)
        status = "✅ 保存" if decision.should_save else "❌ 跳过"
        print(f"'{content[:20]}...'")
        print(f"   决策: {status}")
        print(f"   置信度: {decision.confidence}")
        print(f"   原因: {decision.reason}")
        print()
    
    print(f"会话消息数: {trigger.message_count}")
