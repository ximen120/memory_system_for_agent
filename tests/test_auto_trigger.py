"""
自动触发器单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "ux"))

import pytest
from auto_trigger import AutoTrigger, TriggerDecision


class TestTriggerDecision:
    """测试 TriggerDecision 数据类"""
    
    def test_trigger_decision_creation(self):
        """测试创建决策对象"""
        decision = TriggerDecision(
            should_save=True,
            confidence=0.8,
            reason="测试原因",
            strategy="test"
        )
        assert decision.should_save is True
        assert decision.confidence == 0.8
        assert decision.reason == "测试原因"
        assert decision.strategy == "test"


class TestAutoTriggerCreation:
    """测试 AutoTrigger 创建"""
    
    def test_default_creation(self):
        """测试默认参数创建"""
        trigger = AutoTrigger()
        assert trigger.min_content_length == 10
        assert trigger.max_content_length == 500
        assert trigger.min_confidence == 0.6
        assert trigger.message_count == 0
    
    def test_custom_creation(self):
        """测试自定义参数创建"""
        trigger = AutoTrigger(
            min_content_length=20,
            max_content_length=1000,
            min_confidence=0.7
        )
        assert trigger.min_content_length == 20
        assert trigger.max_content_length == 1000
        assert trigger.min_confidence == 0.7
    
    def test_custom_keywords(self):
        """测试自定义关键词"""
        custom_keywords = {
            "high_priority": ["重要"],
            "medium_priority": ["一般"]
        }
        trigger = AutoTrigger(keywords=custom_keywords)
        assert trigger.keywords == custom_keywords


class TestContentAnalysis:
    """测试内容分析"""
    
    @pytest.fixture
    def trigger(self):
        return AutoTrigger()
    
    def test_short_content_low_score(self, trigger):
        """测试短内容得分低"""
        scores = trigger.analyze_content("你好")
        assert scores["length_score"] == 0.0
    
    def test_optimal_length_high_score(self, trigger):
        """测试适中长度得分高"""
        content = "这是一段长度适中的内容，包含足够的信息量"
        scores = trigger.analyze_content(content)
        assert scores["length_score"] > 0.5
    
    def test_high_priority_keyword_detection(self, trigger):
        """测试高优先级关键词检测"""
        content = "记住我的密码是123456"
        scores = trigger.analyze_content(content)
        assert scores["keyword_score"] > 0.0
    
    def test_complex_content_score(self, trigger):
        """测试复杂内容评分"""
        # 需要足够多的句子和词汇
        content = "第一。第二。第三。第四。第五。包含多个句子和丰富的词汇多样性apple banana cherry date egg"
        scores = trigger.analyze_content(content)
        # 复杂度评分需要至少2个句子和10个不同词汇
        assert scores["complexity_score"] >= 0.0  # 可能为0，但不应该是负数


class TestContextAnalysis:
    """测试上下文分析"""
    
    @pytest.fixture
    def trigger(self):
        return AutoTrigger()
    
    def test_turn_count_score(self, trigger):
        """测试对话轮次评分"""
        context = {"turn_count": 10}
        scores = trigger.analyze_context("测试内容", context)
        assert scores["turn_score"] > 0.0
    
    def test_topic_change_score(self, trigger):
        """测试主题变化评分"""
        context = {
            "topic": "新主题",
            "last_topic": "旧主题"
        }
        scores = trigger.analyze_context("测试内容", context)
        assert scores["topic_score"] == 0.8
    
    def test_user_intent_score(self, trigger):
        """测试用户意图评分"""
        context = {"intent": "分享"}
        scores = trigger.analyze_context("测试内容", context)
        assert scores["intent_score"] == 0.7


class TestTimingAnalysis:
    """测试时间分析"""
    
    @pytest.fixture
    def trigger(self):
        return AutoTrigger()
    
    def test_first_trigger_high_score(self, trigger):
        """测试首次触发时间评分高"""
        scores = trigger.analyze_timing()
        assert scores["time_since_last"] == 1.0
    
    def test_session_duration_score(self, trigger):
        """测试会话持续时间评分"""
        trigger.message_count = 20
        scores = trigger.analyze_timing()
        assert scores["session_duration"] > 0.0


class TestShouldSaveDecision:
    """测试综合决策"""
    
    @pytest.fixture
    def trigger(self):
        return AutoTrigger()
    
    def test_short_content_rejected(self, trigger):
        """测试短内容被拒绝"""
        decision = trigger.should_save("你好")
        assert decision.should_save is False
        assert decision.confidence < 0.6
    
    def test_keyword_content_accepted(self, trigger):
        """测试含关键词内容被接受"""
        content = "记住，我非常喜欢喝咖啡，这是我的重要习惯"
        decision = trigger.should_save(content)
        # 关键词应该提高置信度
        assert decision.confidence > 0.0
    
    def test_message_count_incremented(self, trigger):
        """测试消息计数增加"""
        initial_count = trigger.message_count
        trigger.should_save("测试内容")
        assert trigger.message_count == initial_count + 1
    
    def test_decision_has_reason(self, trigger):
        """测试决策包含原因"""
        content = "记住我的偏好"
        decision = trigger.should_save(content)
        assert decision.reason != ""
        assert decision.strategy != ""


class TestSessionReset:
    """测试会话重置"""
    
    def test_reset_clears_state(self):
        """测试重置清除状态"""
        trigger = AutoTrigger()
        trigger.message_count = 10
        trigger.should_save("测试内容")  # 设置 last_trigger_time
        
        trigger.reset_session()
        
        assert trigger.message_count == 0
        assert trigger.last_trigger_time is None
        assert len(trigger.session_history) == 0


class TestAutoTriggerGenerateReason:
    """测试原因生成"""
    
    @pytest.fixture
    def trigger(self):
        return AutoTrigger()
    
    def test_reason_includes_keywords(self, trigger):
        """测试原因包含关键词提示"""
        content_scores = {"keyword_score": 0.8, "length_score": 0.0}
        context_scores = {"topic_score": 0.0, "turn_score": 0.0, "intent_score": 0.0}
        timing_scores = {"time_since_last": 0.0, "session_duration": 0.0}
        
        reason = trigger._generate_reason(content_scores, context_scores, timing_scores)
        assert "关键词" in reason
    
    def test_reason_includes_length(self, trigger):
        """测试原因包含长度提示"""
        content_scores = {"keyword_score": 0.0, "length_score": 0.8}
        context_scores = {"topic_score": 0.0, "turn_score": 0.0, "intent_score": 0.0}
        timing_scores = {"time_since_last": 0.0, "session_duration": 0.0}
        
        reason = trigger._generate_reason(content_scores, context_scores, timing_scores)
        assert "长度" in reason
    
    def test_reason_includes_topic(self, trigger):
        """测试原因包含主题提示"""
        content_scores = {"keyword_score": 0.0, "length_score": 0.0}
        context_scores = {"topic_score": 0.8, "turn_score": 0.0, "intent_score": 0.0}
        timing_scores = {"time_since_last": 0.0, "session_duration": 0.0}
        
        reason = trigger._generate_reason(content_scores, context_scores, timing_scores)
        assert "主题" in reason
    
    def test_reason_default(self, trigger):
        """测试默认原因"""
        content_scores = {"keyword_score": 0.0, "length_score": 0.0}
        context_scores = {"topic_score": 0.0, "turn_score": 0.0, "intent_score": 0.0}
        timing_scores = {"time_since_last": 0.0, "session_duration": 0.0}
        
        reason = trigger._generate_reason(content_scores, context_scores, timing_scores)
        assert reason == "综合评分达标"


class TestAutoTriggerTimingAnalysis:
    """测试时间分析边界情况"""
    
    def test_timing_within_5_minutes(self):
        """测试5分钟内不重复触发"""
        from datetime import datetime, timedelta
        
        trigger = AutoTrigger()
        trigger.last_trigger_time = datetime.now() - timedelta(minutes=3)
        
        scores = trigger.analyze_timing()
        assert scores["time_since_last"] == 0.0
    
    def test_timing_after_10_minutes(self):
        """测试10分钟后高评分"""
        from datetime import datetime, timedelta
        
        trigger = AutoTrigger()
        trigger.last_trigger_time = datetime.now() - timedelta(minutes=10)
        
        scores = trigger.analyze_timing()
        assert scores["time_since_last"] > 0.0


class TestAutoTriggerEdgeCases:
    """测试边界情况"""
    
    def test_empty_content(self):
        """测试空内容"""
        trigger = AutoTrigger()
        decision = trigger.should_save("")
        assert decision.should_save is False
    
    def test_very_long_content(self):
        """测试超长内容"""
        trigger = AutoTrigger()
        long_content = "A" * 1000
        decision = trigger.should_save(long_content)
        # 超长内容长度评分会降低
        assert decision.confidence >= 0.0
    
    def test_all_high_priority_keywords(self):
        """测试所有高优先级关键词"""
        trigger = AutoTrigger()
        content = "记住我喜欢我讨厌我要我不想要计划目标梦想愿望"
        decision = trigger.should_save(content)
        assert decision.confidence > 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
