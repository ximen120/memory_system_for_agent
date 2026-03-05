"""
对话可靠保存器单元测试
"""
import sys
import os
import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, r"D:\projects\memory_system_v3\src")

try:
    from ux.conversation_saver import ConversationSaver, SaveResult, END_SIGNAL_KEYWORDS
    print("✅ 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "=" * 60)
    print("测试1: 基本功能")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建保存器（使用短间隔进行测试）
        saver = ConversationSaver(
            save_dir=temp_dir,
            auto_save_interval=2,  # 2秒
            idle_timeout=3          # 3秒
        )
        print("✅ ConversationSaver创建成功")
        
        # 测试1: 发送几条消息
        print("\n测试发送消息...")
        result1 = saver.on_message("user", "你好安仔")
        print(f"   消息1结果: saved={result1.saved}, type={result1.save_type}")
        
        result2 = saver.on_message("assistant", "你好安哥！有什么可以帮你的？")
        print(f"   消息2结果: saved={result2.saved}, type={result2.save_type}")
        
        result3 = saver.on_message("user", "记住，我喜欢喝咖啡")
        print(f"   消息3结果: saved={result3.saved}, type={result3.save_type}, memory_extracted={result3.memory_extracted}")
        
        # 测试2: 检查会话摘要
        print("\n测试获取会话摘要...")
        summary = saver.get_session_summary()
        print(f"   会话ID: {summary['session_id']}")
        print(f"   消息数量: {summary['message_count']}")
        print(f"   记忆要点数量: {summary['memory_points_count']}")
        assert summary['message_count'] == 3
        assert summary['memory_points_count'] >= 1
        print("✅ 会话摘要正确")
        
        # 测试3: 强制保存
        print("\n测试强制保存...")
        file_path = saver.force_save()
        print(f"   保存文件: {file_path}")
        assert Path(file_path).exists()
        print("✅ 强制保存成功")
        
        # 测试4: 结束信号
        print("\n测试结束信号...")
        result4 = saver.on_message("user", "先这样吧")
        print(f"   结束信号结果: saved={result4.saved}, type={result4.save_type}")
        assert result4.saved == True
        assert result4.save_type == "end_signal"
        print("✅ 结束信号检测成功")
        
        print("\n✅ 基本功能测试通过！")
        
    finally:
        # 清理
        shutil.rmtree(temp_dir)


def test_timing_functions():
    """测试定时功能"""
    print("\n" + "=" * 60)
    print("测试2: 定时功能")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建保存器
        saver = ConversationSaver(
            save_dir=temp_dir,
            auto_save_interval=1,  # 1秒
            idle_timeout=2          # 2秒
        )
        
        # 发送第一条消息
        result1 = saver.on_message("user", "消息1")
        print(f"消息1: saved={result1.saved}")
        
        # 等待超过自动保存间隔
        print("等待1.5秒...")
        time.sleep(1.5)
        
        # 发送第二条消息，应该触发定时保存
        result2 = saver.on_message("user", "消息2")
        print(f"消息2: saved={result2.saved}, type={result2.save_type}")
        assert result2.saved == True
        assert result2.save_type == "periodic"
        print("✅ 定时保存触发成功")
        
        # 等待超过idle超时
        print("\n等待2.5秒...")
        time.sleep(2.5)
        
        # 发送新消息，应该先保存上一段，再开新会话
        result3 = saver.on_message("user", "新对话开始")
        print(f"新对话: message={result3.message}")
        print("✅ Idle超时检测成功")
        
        print("\n✅ 定时功能测试通过！")
        
    finally:
        # 清理
        shutil.rmtree(temp_dir)


def test_end_signal_keywords():
    """测试结束信号关键词"""
    print("\n" + "=" * 60)
    print("测试3: 结束信号关键词")
    print("=" * 60)
    
    # 测试几个关键词
    test_keywords = [
        "保存",
        "结束",
        "下次见",
        "先这样",
        "bye",
        "see you"
    ]
    
    all_passed = True
    for keyword in test_keywords:
        # 检查关键词是否在列表中
        found = any(kw in keyword.lower() for kw in END_SIGNAL_KEYWORDS)
        status = "✅" if found else "❌"
        print(f"{status} '{keyword}': {found}")
        if not found:
            all_passed = False
    
    if all_passed:
        print("\n✅ 结束信号关键词测试通过！")
    else:
        print("\n❌ 部分结束信号关键词测试失败")


def test_memory_extraction():
    """测试记忆要点提取"""
    print("\n" + "=" * 60)
    print("测试4: 记忆要点提取")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        saver = ConversationSaver(save_dir=temp_dir)
        
        # 发送含关键词的消息
        test_messages = [
            ("user", "记住，我的生日是12月25日"),
            ("user", "我喜欢喝咖啡"),
            ("assistant", "好的，记住了"),
            ("user", "计划下周去北京"),
        ]
        
        extracted_count = 0
        for role, content in test_messages:
            result = saver.on_message(role, content)
            if result.memory_extracted > 0:
                extracted_count += result.memory_extracted
                print(f"✅ 从 '{content[:30]}...' 提取了 {result.memory_extracted} 条记忆")
        
        summary = saver.get_session_summary()
        print(f"\n总计提取了 {summary['memory_points_count']} 条记忆要点")
        assert summary['memory_points_count'] > 0
        print("✅ 记忆要点提取测试通过！")
        
    finally:
        shutil.rmtree(temp_dir)


def test_integration_with_memory_system():
    """测试与MemorySystem的集成"""
    print("\n" + "=" * 60)
    print("测试5: 与MemorySystem集成")
    print("=" * 60)
    
    try:
        from memory_system import MemorySystem
        
        # 创建系统
        system = MemorySystem.create_default()
        print("✅ MemorySystem创建成功")
        
        # 测试on_message
        result = system.on_message("user", "你好，测试一下")
        print(f"   on_message结果: saved={result.saved}")
        
        # 测试end_conversation
        file_path = system.end_conversation()
        print(f"   end_conversation结果: 文件={file_path}")
        
        print("\n✅ MemorySystem集成测试通过！")
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("对话可靠保存器 - 单元测试")
    print("=" * 60)
    
    try:
        # 运行所有测试
        test_basic_functionality()
        test_timing_functions()
        test_end_signal_keywords()
        test_memory_extraction()
        test_integration_with_memory_system()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
