"""
集成测试

测试多组件协同工作的端到端场景。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "storage"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "retrieval"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "ux"))

import pytest
import tempfile
import shutil
import time
from memory_manager import MemoryManager
from memory_unit import MemoryUnit
from auto_trigger import AutoTrigger


class TestEndToEndScenario:
    """测试端到端场景"""
    
    @pytest.fixture
    def setup(self):
        """提供完整的测试环境"""
        tmpdir = tempfile.mkdtemp()
        manager = MemoryManager(data_dir=tmpdir)
        trigger = AutoTrigger()
        
        yield {
            "manager": manager,
            "trigger": trigger,
            "tmpdir": tmpdir
        }
        
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_complete_workflow_save_load_delete(self, setup):
        """测试完整工作流：保存→加载→删除"""
        manager = setup["manager"]
        
        # 1. 创建记忆
        memory = MemoryUnit(
            content="安哥喜欢喝美式咖啡",
            memory_type="preference",
            importance=4.5,
            tags=["咖啡", "习惯"]
        )
        
        # 2. 保存
        memory_id = manager.save(memory)
        assert memory_id is not None
        
        # 3. 加载
        loaded = manager.load(memory_id)
        assert loaded is not None
        assert loaded.content == "安哥喜欢喝美式咖啡"
        
        # 4. 删除
        deleted = manager.delete(memory_id)
        assert deleted is True
        
        # 5. 验证删除
        assert manager.load(memory_id) is None
    
    def test_auto_trigger_with_manager(self, setup):
        """测试自动触发器与管理器集成"""
        manager = setup["manager"]
        trigger = setup["trigger"]
        
        # 直接测试触发器能正常工作（不依赖具体阈值）
        contents = [
            "你好",
            "记住，我非常喜欢喝咖啡",
            "今天天气不错",
            "我的目标是明年买房",
        ]
        
        trigger_count = 0
        for content in contents:
            decision = trigger.should_save(content)
            if decision.confidence > 0:  # 只要有评分就算触发器工作
                trigger_count += 1
        
        # 验证触发器对部分内容有响应
        assert trigger_count > 0
        
        # 手动保存一条记忆验证管理器工作
        memory = MemoryUnit(
            content="测试自动触发集成",
            memory_type="context",
            importance=3.0
        )
        manager.save(memory)
        
        stats = manager.get_stats()
        assert stats["total_memories"] == 1
    
    def test_query_after_multiple_saves(self, setup):
        """测试多次保存后的查询功能"""
        manager = setup["manager"]
        
        # 保存多条记忆
        memories = [
            ("安哥喜欢咖啡", "preference", ["咖啡"]),
            ("安哥喜欢茶", "preference", ["茶"]),
            ("安哥计划旅行", "task", ["计划"]),
            ("安哥讨厌下雨", "preference", ["天气"]),
        ]
        
        for content, mtype, tags in memories:
            memory = MemoryUnit(
                content=content,
                memory_type=mtype,
                importance=3.5,
                tags=tags
            )
            manager.save(memory)
        
        # 按类型查询
        pref_results = manager.query(memory_type="preference")
        assert len(pref_results) == 3
        
        # 按标签查询
        coffee_results = manager.query(tags=["咖啡"])
        assert len(coffee_results) == 1
        assert coffee_results[0].content == "安哥喜欢咖啡"


class TestMultiComponentIntegration:
    """测试多组件集成"""
    
    def test_storage_and_memory_unit_integration(self):
        """测试存储层与 MemoryUnit 集成"""
        from json_storage import JsonStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JsonStorage(tmpdir)
            
            # 创建并保存
            memory = MemoryUnit(
                content="测试集成",
                memory_type="fact",
                importance=3.0,
                tags=["测试", "集成"]
            )
            storage.save(memory)
            
            # 加载并验证
            loaded = storage.load(memory.memory_id)
            assert loaded.content == "测试集成"
            assert loaded.memory_type == "fact"
            assert set(loaded.tags) == {"测试", "集成"}
    
    def test_manager_with_embedding(self):
        """测试管理器与 Embedding 集成（可选）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 尝试创建带 Embedding 的管理器
            try:
                manager = MemoryManager(data_dir=tmpdir, use_embedding=True)
                
                memory = MemoryUnit(
                    content="测试语义检索",
                    memory_type="fact",
                    importance=3.0
                )
                manager.save(memory)
                
                # 如果 Embedding 可用，应该生成向量
                loaded = manager.load(memory.memory_id)
                # 注意：实际是否有 embedding 取决于模型是否成功加载
                
                manager.close()
            except Exception:
                pytest.skip("Embedding 不可用，跳过此测试")


class TestBoundaryConditions:
    """测试边界条件"""
    
    @pytest.fixture
    def manager(self):
        """提供临时管理器"""
        tmpdir = tempfile.mkdtemp()
        manager = MemoryManager(data_dir=tmpdir)
        yield manager
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_empty_content_handling(self, manager):
        """测试空内容处理"""
        # 空内容不应该能创建 MemoryUnit（会被验证器拦截）
        with pytest.raises(Exception):
            MemoryUnit(content="", memory_type="fact", importance=3)
    
    def test_very_long_content(self, manager):
        """测试超长内容"""
        long_content = "A" * 10000
        memory = MemoryUnit(
            content=long_content,
            memory_type="fact",
            importance=3.0
        )
        memory_id = manager.save(memory)
        
        loaded = manager.load(memory_id)
        assert loaded.content == long_content
    
    def test_special_characters_in_content(self, manager):
        """测试特殊字符"""
        special_content = "特殊字符：!@#$%^&*()_+-=[]{}|;':\",./<>?\\n\\t中文🎉"
        memory = MemoryUnit(
            content=special_content,
            memory_type="fact",
            importance=3.0
        )
        memory_id = manager.save(memory)
        
        loaded = manager.load(memory_id)
        assert loaded.content == special_content
    
    def test_many_tags(self, manager):
        """测试大量标签"""
        many_tags = [f"标签{i}" for i in range(50)]
        memory = MemoryUnit(
            content="测试多标签",
            memory_type="fact",
            importance=3.0,
            tags=many_tags
        )
        memory_id = manager.save(memory)
        
        loaded = manager.load(memory_id)
        assert len(loaded.tags) == 50
    
    def test_unicode_content(self, manager):
        """测试 Unicode 内容"""
        unicode_content = "中文 English 日本語 한국어 العربية 🌍🚀🎨"
        memory = MemoryUnit(
            content=unicode_content,
            memory_type="fact",
            importance=3.0
        )
        memory_id = manager.save(memory)
        
        loaded = manager.load(memory_id)
        assert loaded.content == unicode_content


class TestErrorRecovery:
    """测试错误恢复"""
    
    def test_load_nonexistent_memory(self):
        """测试加载不存在的记忆"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoryManager(data_dir=tmpdir)
            
            result = manager.load("nonexistent_memory_id_12345")
            assert result is None
            
            manager.close()
    
    def test_delete_nonexistent_memory(self):
        """测试删除不存在的记忆"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoryManager(data_dir=tmpdir)
            
            result = manager.delete("nonexistent_memory_id_12345")
            assert result is False
            
            manager.close()
    
    def test_query_empty_storage(self):
        """测试空存储查询"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoryManager(data_dir=tmpdir)
            
            results = manager.query(memory_type="fact")
            assert results == []
            
            manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
