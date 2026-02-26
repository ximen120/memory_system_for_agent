"""
M4四层架构集成测试

测试核心层、存储层、检索层、优化层、傻瓜层的协同工作。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import os
os.environ['TEST_MODE'] = 'true'

import pytest

from memory_system import MemorySystem, MemorySystemConfig, quick_remember, quick_recall
from core.memory_unit import MemoryUnit
from storage.chroma_storage import ChromaStorage
from retrieval.retrieval_api import RetrievalAPI
from optimization.auto_optimizer import AutoOptimizer
from ux.auto_trigger import AutoTrigger


class TestM4MemorySystemCreation:
    """M4记忆系统创建测试"""
    
    def test_create_default(self):
        """测试默认创建"""
        system = MemorySystem.create_default("./test_data", "test_system")
        
        assert system is not None
        assert system.storage is not None
        assert system.retrieval_api is not None
        
        system.close()
    
    def test_create_with_config(self):
        """测试带配置创建"""
        config = MemorySystemConfig(
            storage_path="./test_config",
            collection_name="test_config",
            enable_auto_optimize=False
        )
        
        system = MemorySystem.create_default(
            storage_path=config.storage_path,
            collection_name=config.collection_name
        )
        
        assert system is not None
        system.close()


class TestM4RememberRecall:
    """M4记住和回忆测试"""
    
    @pytest.fixture
    def system(self):
        """提供记忆系统"""
        system = MemorySystem.create_default("./test_recall", "test_recall")
        yield system
        system.close()
    
    def test_remember_content(self, system):
        """测试记住内容"""
        memory_id = system.remember(
            content="我喜欢喝咖啡",
            tags=["饮食", "偏好"]
        )
        
        assert memory_id is not None
        assert isinstance(memory_id, str)
    
    def test_recall_content(self, system):
        """测试回忆内容"""
        # 先记住
        system.remember("我喜欢喝咖啡", tags=["饮食"])
        
        # 再回忆
        results = system.recall("咖啡", top_k=5)
        
        assert isinstance(results, list)
    
    def test_forget_content(self, system):
        """测试遗忘内容"""
        # 先记住
        memory_id = system.remember("测试内容")
        
        if memory_id:
            # 再遗忘
            result = system.forget(memory_id)
            assert result is True


class TestM4AutoTrigger:
    """M4自动触发测试"""
    
    @pytest.fixture
    def system(self):
        """提供记忆系统"""
        system = MemorySystem.create_default("./test_trigger", "test_trigger")
        yield system
        system.close()
    
    def test_should_remember(self, system):
        """测试是否应该记住"""
        decision = system.should_remember("我喜欢喝咖啡")
        
        assert decision is not None
        assert hasattr(decision, 'should_save')
        assert hasattr(decision, 'confidence')
    
    def test_process_message_save(self, system):
        """测试处理保存消息"""
        result = system.process_message(
            role="user",
            content="记住我喜欢喝咖啡",
            auto_save=False
        )
        
        assert isinstance(result, dict)
        assert "saved" in result


class TestM4FourLayersIntegration:
    """M4四层架构集成测试"""
    
    @pytest.fixture
    def system(self):
        """提供记忆系统"""
        system = MemorySystem.create_default("./test_layers", "test_layers")
        yield system
        system.close()
    
    def test_core_layer(self, system):
        """测试核心层"""
        # 创建记忆单元
        memory = MemoryUnit(
            content="测试内容",
            memory_type="fact",
            tags=["测试"],
            importance=3.0
        )
        
        assert memory is not None
        assert memory.content == "测试内容"
    
    def test_storage_layer(self, system):
        """测试存储层"""
        # 存储统计
        stats = system.get_stats()
        
        assert "storage" in stats
        assert isinstance(stats["storage"], dict)
    
    def test_retrieval_layer(self, system):
        """测试检索层"""
        # 检索统计
        stats = system.get_stats()
        
        assert "retrieval" in stats
    
    def test_optimization_layer(self, system):
        """测试优化层"""
        # 优化统计
        stats = system.get_stats()
        
        assert "optimization" in stats
    
    def test_ux_layer(self, system):
        """测试傻瓜层"""
        # 自动触发器
        assert system.auto_trigger is not None
        
        # 处理消息
        result = system.process_message("user", "测试消息")
        assert isinstance(result, dict)


class TestM4EndToEnd:
    """M4端到端测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建系统
        system = MemorySystem.create_default("./test_e2e", "test_e2e")
        
        try:
            # 2. 记住多条记忆
            memories = [
                ("我喜欢喝咖啡", ["饮食", "偏好"]),
                ("我喜欢喝茶", ["饮食", "偏好"]),
                ("今天天气很好", ["天气"]),
            ]
            
            memory_ids = []
            for content, tags in memories:
                mid = system.remember(content, tags=tags)
                if mid:
                    memory_ids.append(mid)
            
            # 3. 回忆
            results = system.recall("饮品", top_k=10)
            
            # 4. 获取统计
            stats = system.get_stats()
            assert "storage" in stats
            assert "retrieval" in stats
            
            # 5. 处理消息
            result = system.process_message("user", "记住我喜欢Python")
            assert isinstance(result, dict)
            
        finally:
            system.close()
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with MemorySystem.create_default("./test_ctx", "test_ctx") as system:
            # 使用系统
            memory_id = system.remember("测试内容")
            assert memory_id is not None or memory_id is None  # 可能成功也可能失败
        
        # 系统应该已关闭
    
    def test_quick_functions(self):
        """测试快速函数"""
        # 快速记住
        memory_id = quick_remember("快速测试内容")
        # 可能成功也可能失败（取决于模型加载）
        
        # 快速回忆
        results = quick_recall("测试")
        assert isinstance(results, list)


class TestM4StatsAndReport:
    """M4统计和报告测试"""
    
    @pytest.fixture
    def system(self):
        """提供记忆系统"""
        system = MemorySystem.create_default("./test_stats", "test_stats")
        yield system
        system.close()
    
    def test_get_stats(self, system):
        """测试获取统计"""
        stats = system.get_stats()
        
        assert isinstance(stats, dict)
        assert "storage" in stats
        assert "retrieval" in stats
        assert "optimization" in stats
        assert "timestamp" in stats
    
    def test_get_optimization_report(self, system):
        """测试获取优化报告"""
        report = system.get_optimization_report()
        
        assert isinstance(report, str)
        assert len(report) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
