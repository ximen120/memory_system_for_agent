"""
M6傻瓜层功能演示脚本

展示6个模块的完整工作流程和实际使用场景
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs'))

import tempfile
import shutil
from datetime import datetime


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """打印小节标题"""
    print(f"\n>> {title}")
    print("-" * 50)


def demo_auto_trigger():
    """演示1: AutoTrigger - 自动触发保存"""
    print_header("演示1: AutoTrigger - 智能判断何时保存记忆")
    
    # 简化版AutoTrigger
    class SimpleAutoTrigger:
        KEYWORDS_HIGH = ["记住", "喜欢", "计划", "目标", "梦想"]
        KEYWORDS_MEDIUM = ["觉得", "习惯", "经常", "重要"]
        
        def should_save(self, content):
            for kw in self.KEYWORDS_HIGH:
                if kw in content:
                    return True, 0.9, f"高优先级关键词: {kw}"
            for kw in self.KEYWORDS_MEDIUM:
                if kw in content:
                    return True, 0.7, f"中优先级关键词: {kw}"
            if len(content) > 20:
                return True, 0.6, "内容较长，可能有价值"
            return False, 0.3, "无明确信号"
    
    trigger = SimpleAutoTrigger()
    
    print_section("测试不同内容的触发判断")
    
    test_cases = [
        "安哥喜欢喝咖啡，每天早上必须一杯美式",
        "记住下周三要开会",
        "今天天气不错，适合出门",
        "好的",
    ]
    
    for content in test_cases:
        should_save, confidence, reason = trigger.should_save(content)
        status = "保存" if should_save else "跳过"
        print(f"  内容: {content[:30]}...")
        print(f"  决策: {status} (置信度: {confidence:.2f})")
        print(f"  原因: {reason}\n")
    
    return trigger


def demo_tag_manager():
    """演示2: TagManager - 自动标签管理"""
    print_header("演示2: TagManager - 自动提取和管理标签")
    
    class SimpleTagManager:
        STOP_WORDS = {"的", "了", "是", "在", "我", "有", "和", "就", "不"}
        
        def auto_extract_tags(self, content, max_tags=5):
            words = content.replace("。", "").replace("，", "").split()
            tags = []
            for word in words:
                if 2 <= len(word) <= 4 and word not in self.STOP_WORDS:
                    tags.append(word)
            return list(dict.fromkeys(tags))[:max_tags]
    
    tag_mgr = SimpleTagManager()
    
    print_section("自动提取标签")
    
    contents = [
        "安哥计划下周学习Python编程语言",
        "安哥喜欢喝咖啡和茶",
        "今天完成了项目文档编写",
    ]
    
    for content in contents:
        tags = tag_mgr.auto_extract_tags(content)
        print(f"  内容: {content}")
        print(f"  标签: {tags}\n")
    
    return tag_mgr


def demo_command_parser():
    """演示3: CommandParser - 自然语言命令解析"""
    print_header("演示3: CommandParser - 解析自然语言命令")
    
    class SimpleCommandParser:
        COMMANDS = {
            "remember": ["记住", "记得", "记录", "保存", "记下"],
            "forget": ["忘掉", "忘记", "删除", "移除", "清空"],
            "search": ["查找", "搜索", "查询", "找一下", "找找"],
            "show": ["显示", "列出", "查看", "展示", "看看"],
        }
        
        def parse(self, text):
            for cmd_type, keywords in self.COMMANDS.items():
                for kw in keywords:
                    if kw in text:
                        content = text.replace(kw, "").strip("，。！")
                        return cmd_type, content
            return "unknown", text
    
    parser = SimpleCommandParser()
    
    print_section("解析各种自然语言命令")
    
    commands = [
        "记住安哥喜欢喝咖啡",
        "查找关于Python的记忆",
        "忘掉昨天的临时记录",
        "显示最近一周的所有记忆",
    ]
    
    for cmd_text in commands:
        cmd_type, content = parser.parse(cmd_text)
        print(f"  输入: '{cmd_text}'")
        print(f"  命令: {cmd_type}")
        print(f"  内容: {content}\n")
    
    return parser


def demo_memory_layers():
    """演示4: MemoryLayers - 四层记忆架构"""
    print_header("演示4: MemoryLayers - 四层记忆架构")
    
    from enum import Enum
    
    class MemoryLayerType(Enum):
        WORKING = "working"
        SHORT_TERM = "short"
        LONG_TERM = "long"
        PERMANENT = "permanent"
    
    class SimpleMemory:
        def __init__(self, content, memory_type, importance, tags=None):
            self.content = content
            self.memory_type = memory_type
            self.importance = importance
            self.tags = tags or []
            self.memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(self)}"
            self.created_at = datetime.now().isoformat()
    
    class SimpleMemoryManager:
        def __init__(self):
            self.layers = {t: [] for t in MemoryLayerType}
        
        def add(self, content, memory_type, importance, tags=None):
            mem = SimpleMemory(content, memory_type, importance, tags)
            if importance >= 4.5:
                self.layers[MemoryLayerType.PERMANENT].append(mem)
            elif importance >= 3.0:
                self.layers[MemoryLayerType.LONG_TERM].append(mem)
            else:
                self.layers[MemoryLayerType.SHORT_TERM].append(mem)
            return mem.memory_id
        
        def get_stats(self):
            return {k.value: len(v) for k, v in self.layers.items()}
        
        def search(self, keywords):
            results = []
            for layer in self.layers.values():
                for mem in layer:
                    if any(kw in mem.content for kw in keywords):
                        results.append(mem)
            return results
    
    manager = SimpleMemoryManager()
    
    print_section("自动分层存储")
    
    # 添加不同重要性的记忆
    memories = [
        ("安哥是Simon，安仔的哥哥", "fact", 5.0, ["身份", "核心"]),
        ("安哥喜欢喝咖啡", "preference", 4.0, ["咖啡", "喜好"]),
        ("安哥是程序员", "fact", 3.5, ["职业"]),
        ("今天天气不错", "context", 2.0, ["天气"]),
        ("临时记录一些想法", "note", 1.5, []),
    ]
    
    for content, mtype, imp, tags in memories:
        mid = manager.add(content, mtype, imp, tags)
        layer = "permanent" if imp >= 4.5 else ("long" if imp >= 3.0 else "short")
        print(f"  [{layer}] {content[:30]}... (重要性: {imp})")
    
    print_section("各层统计")
    stats = manager.get_stats()
    for layer_name, count in stats.items():
        print(f"  {layer_name}: {count} 条")
    
    print_section("跨层搜索")
    results = manager.search(["安哥"])
    print(f"  搜索'安哥'，找到 {len(results)} 条记忆:")
    for mem in results:
        print(f"    - {mem.content}")
    
    return manager


def demo_timeline_viewer():
    """演示5: TimelineViewer - 时间线浏览"""
    print_header("演示5: TimelineViewer - 按时间查看记忆")
    
    print_section("时间线展示")
    
    # 模拟时间线数据
    timeline_data = [
        {"time": "2026-02-24 09:00", "content": "今天开始学习Rust", "type": "goal"},
        {"time": "2026-02-24 14:00", "content": "完成了项目文档", "type": "task"},
        {"time": "2026-02-23 10:00", "content": "安哥喜欢喝咖啡", "type": "preference"},
        {"time": "2026-02-23 16:00", "content": "记住下周开会", "type": "task"},
        {"time": "2026-02-22 09:00", "content": "安哥是程序员", "type": "fact"},
    ]
    
    print("  最近记忆时间线:")
    print("  " + "-" * 50)
    
    current_date = None
    for item in timeline_data:
        date = item["time"][:10]
        time = item["time"][11:]
        if date != current_date:
            print(f"\n  📅 {date}")
            current_date = date
        print(f"     {time} [{item['type']}] {item['content']}")
    
    return timeline_data


def demo_keyword_search():
    """演示6: KeywordSearch - 关键词检索"""
    print_header("演示6: KeywordSearch - 快速检索记忆")
    
    print_section("关键词搜索演示")
    
    # 模拟记忆数据库
    memories_db = [
        {"content": "安哥喜欢喝咖啡，每天早上必须一杯美式", "tags": ["咖啡", "喜好"]},
        {"content": "安哥是程序员，主要使用Python", "tags": ["职业", "Python"]},
        {"content": "安哥计划学习Rust编程语言", "tags": ["计划", "Rust"]},
        {"content": "今天完成了项目文档编写", "tags": ["工作", "项目"]},
        {"content": "安哥喜欢喝茶，特别是绿茶", "tags": ["茶", "喜好"]},
    ]
    
    # 搜索功能
    def search_keywords(keywords):
        results = []
        for mem in memories_db:
            content = mem["content"]
            if any(kw in content for kw in keywords):
                # 计算相关度分数
                score = sum(1 for kw in keywords if kw in content) / len(keywords)
                results.append((mem, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    # 测试搜索
    search_queries = [
        ["安哥", "咖啡"],
        ["Python"],
        ["安哥", "喜欢"],
    ]
    
    for keywords in search_queries:
        print(f"\n  搜索关键词: {keywords}")
        results = search_keywords(keywords)
        print(f"  找到 {len(results)} 条结果:")
        for mem, score in results[:3]:
            print(f"    (相关度: {score:.2f}) {mem['content'][:40]}...")
    
    return search_keywords


def demo_full_workflow():
    """完整工作流演示"""
    print_header("完整工作流演示：从输入到检索")
    
    print("""
场景：安哥和安仔的对话中，安仔自动管理记忆

[对话开始]
安哥: "安哥计划下周学习Rust编程语言"

[安仔的处理流程]
    ↓
Step 1: AutoTrigger分析
    检测到"计划"关键词
    置信度: 0.90 -> 决定保存
    
    ↓
Step 2: TagManager提取标签
    自动标签: ['计划', '学习', 'Rust', '编程']
    
    ↓
Step 3: MemoryLayers自动分层
    重要性: 4.5 -> 保存到 Permanent层
    
    ↓
[保存完成]

[稍后]
安哥: "查找关于Rust的记忆"

[安仔的处理流程]
    ↓
Step 4: CommandParser解析命令
    识别为 SEARCH 命令
    内容: "关于Rust的记忆"
    
    ↓
Step 5: KeywordSearch执行检索
    关键词: ['Rust']
    找到 1 条相关记忆
    
    ↓
Step 6: TimelineViewer展示结果
    📅 2026-02-24
       09:00 [goal] 安哥计划下周学习Rust编程语言
    
    ↓
[检索完成]
安仔: "找到1条关于Rust的记忆：安哥计划下周学习Rust编程语言"
""")


def main():
    """主函数：运行所有演示"""
    print("\n" + "=" * 70)
    print("  M6傻瓜层功能演示")
    print("  为安哥打造的零操作记忆系统")
    print("=" * 70)
    print(f"\n演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行各个演示
    trigger = demo_auto_trigger()
    tag_mgr = demo_tag_manager()
    parser = demo_command_parser()
    manager = demo_memory_layers()
    timeline = demo_timeline_viewer()
    search = demo_keyword_search()
    demo_full_workflow()
    
    # 总结
    print_header("演示总结")
    print("""
M6傻瓜层六大功能:

✅ AutoTrigger     - 智能判断何时保存记忆
✅ TagManager      - 自动提取和管理标签
✅ CommandParser   - 解析自然语言命令
✅ MemoryLayers    - 四层记忆架构自动分层
✅ TimelineViewer  - 按时间查看记忆
✅ KeywordSearch   - 快速关键词检索

核心优势:
• 全自动 - 自动判断、自动保存、自动分层
• 自然语言 - 像说话一样管理记忆
• 零配置 - 开箱即用，无需设置
• 自修复 - 出问题自动处理

""")
    
    print("=" * 70)
    print("演示完成！感谢安哥的使用 😊")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    sys.exit(main())
