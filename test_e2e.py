"""
记忆系统v3 端到端功能测试
测试核心流程：add → persist → reload → search → delete
"""
import sys
import os
import shutil
import tempfile

sys.path.insert(0, 'D:\\projects\\memory_system_v3\\src')

def test_full_lifecycle():
    """测试完整生命周期"""
    test_dir = os.path.join(tempfile.gettempdir(), 'memory_test_e2e')
    
    # 清理旧测试数据
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    print("=" * 60)
    print("记忆系统v3 端到端功能测试")
    print("=" * 60)
    
    results = []
    
    # ========== 测试1：基本初始化 ==========
    try:
        from api.memory_api import MemoryAPI
        api = MemoryAPI(data_dir=test_dir)
        print("\n[测试1] MemoryAPI初始化: PASS")
        results.append(("初始化", True))
    except Exception as e:
        print(f"\n[测试1] MemoryAPI初始化: FAIL - {e}")
        results.append(("初始化", False))
        return results
    
    # ========== 测试2：添加记忆 ==========
    try:
        mid1 = api.add_memory("安哥喜欢喝咖啡", memory_type="preference", importance=4.0, tags=["安哥", "偏好"])
        mid2 = api.add_memory("每天早上9点开始训练", memory_type="fact", importance=3.5, tags=["训练", "日程"])
        mid3 = api.add_memory("五部经典：易经、道德经、论语、孙子兵法、金刚经", memory_type="fact", importance=5.0, tags=["经典", "核心"])
        print(f"[测试2] 添加3条记忆: PASS (ids: {mid1[:20]}..., {mid2[:20]}..., {mid3[:20]}...)")
        results.append(("添加记忆", True))
    except Exception as e:
        print(f"[测试2] 添加记忆: FAIL - {e}")
        results.append(("添加记忆", False))
        return results
    
    # ========== 测试3：持久化文件检查 ==========
    try:
        storage_dir = os.path.join(test_dir, "memories")
        files = os.listdir(storage_dir) if os.path.exists(storage_dir) else []
        json_files = [f for f in files if f.endswith('.json')]
        assert len(json_files) >= 3, f"期望至少3个json文件，实际{len(json_files)}"
        print(f"[测试3] 持久化文件检查: PASS ({len(json_files)}个json文件)")
        results.append(("持久化文件", True))
    except Exception as e:
        print(f"[测试3] 持久化文件检查: FAIL - {e}")
        results.append(("持久化文件", False))
    
    # ========== 测试4：重启后加载 ==========
    try:
        api2 = MemoryAPI(data_dir=test_dir)
        memory_count = len(api2._memories)
        assert memory_count >= 3, f"期望至少3条记忆，实际{memory_count}"
        assert mid1 in api2._memories, f"记忆{mid1}未加载"
        print(f"[测试4] 重启后加载: PASS ({memory_count}条记忆)")
        results.append(("重启加载", True))
    except Exception as e:
        print(f"[测试4] 重启后加载: FAIL - {e}")
        results.append(("重启加载", False))
    
    # ========== 测试5：搜索功能 ==========
    try:
        search_results = api2.search("咖啡", top_k=5)
        print(f"[测试5] 搜索'咖啡': PASS (返回{len(search_results)}条结果)")
        results.append(("搜索功能", True))
    except Exception as e:
        print(f"[测试5] 搜索'咖啡': FAIL - {e}")
        results.append(("搜索功能", False))
    
    # ========== 测试6：删除记忆 ==========
    try:
        api2.delete_memory(mid2)
        assert mid2 not in api2._memories, "删除后内存中仍存在"
        # 重启验证删除持久化
        api3 = MemoryAPI(data_dir=test_dir)
        assert mid2 not in api3._memories, "重启后删除的记忆又出现了"
        print(f"[测试6] 删除记忆+持久化: PASS")
        results.append(("删除持久化", True))
    except Exception as e:
        print(f"[测试6] 删除记忆: FAIL - {e}")
        results.append(("删除持久化", False))
    
    # ========== 测试7：宽容模式（旧数据导入） ==========
    try:
        from core.memory_unit import MemoryUnit
        legacy = {"content": "", "importance": 0, "memory_type": "unknown_type"}
        unit = MemoryUnit.from_legacy_dict(legacy)
        assert unit.content == "[空记忆]"
        assert unit.importance == 1.0
        assert unit.memory_type == "fact"
        print(f"[测试7] 宽容模式旧数据导入: PASS")
        results.append(("宽容模式", True))
    except Exception as e:
        print(f"[测试7] 宽容模式: FAIL - {e}")
        results.append(("宽容模式", False))
    
    # ========== 测试8：离线模式配置 ==========
    try:
        from retrieval.embedding_service import EmbeddingConfig
        cfg = EmbeddingConfig()
        assert cfg.offline == True, f"offline应为True，实际{cfg.offline}"
        print(f"[测试8] 离线模式默认配置: PASS")
        results.append(("离线模式", True))
    except Exception as e:
        print(f"[测试8] 离线模式: FAIL - {e}")
        results.append(("离线模式", False))
    
    # ========== 总结 ==========
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    for name, r in results:
        status = "PASS" if r else "FAIL"
        print(f"  {'✅' if r else '❌'} {name}: {status}")
    print(f"\n总计: {len(results)}项, 通过: {passed}, 失败: {failed}")
    
    if failed == 0:
        print("\n✅ 全部通过，可以升级！")
    else:
        print("\n❌ 有失败项，需要修复后再升级")
    
    # 清理
    shutil.rmtree(test_dir, ignore_errors=True)
    
    return results

if __name__ == "__main__":
    test_full_lifecycle()
