#!/usr/bin/env python
"""
记忆系统 v3.0 快速测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.unified_api import UnifiedAPI


def main():
    print("🚀 记忆系统 v3.0 启动测试")
    print("=" * 60)
    
    try:
        # 创建API实例
        api = UnifiedAPI()
        print("✅ API实例创建成功")
        
        # 测试1: 保存记忆
        memory_id = api.remember('安哥喜欢喝美式咖啡', importance=4.0, tags=['咖啡', '喜好'])
        print(f"✅ 保存记忆: {memory_id[:8]}...")
        
        # 测试2: 查询记忆
        results = api.recall('咖啡')
        print(f"✅ 查询记忆: 找到 {len(results)} 条")
        
        # 测试3: 查看统计
        stats = api.get_stats()
        print(f"✅ 系统统计: {stats}")
        
        print("=" * 60)
        print("🎉 系统启动成功！可以开始使用了")
        print()
        print("使用方法:")
        print("  1. 命令行: python start_memory_system.py")
        print("  2. Python代码: from api.unified_api import UnifiedAPI")
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
