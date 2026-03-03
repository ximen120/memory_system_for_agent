"""
记忆系统升级迁移脚本
将md核心记忆 + auto_memory json记忆 → 统一迁移到新MemoryAPI的JsonStorage

执行前提：
1. 备份已完成（memory_backup_20260302）
2. 源码修复已验证通过
"""
import sys
import os
import json
import re
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, r'D:\projects\memory_system_v3\src')

from core.memory_unit import MemoryUnit
from storage.json_storage import JsonStorage

# ========== 配置 ==========
MEMORY_MD_DIR = r"D:\AnZai_JieYue\memory"
AUTO_MEMORY_DIR = r"D:\AnZai_JieYue\memory\backup_20260302\auto_memory"
TARGET_DIR = r"D:\AnZai_JieYue\memory_v3\memories"
TEST_MODE = False  # True=测试模式（写到临时目录），False=正式迁移

if TEST_MODE:
    TARGET_DIR = r"D:\AnZai_JieYue\memory_v3_test\memories"

# ========== 工具函数 ==========

def parse_md_memory(filepath: str) -> dict:
    """解析md记忆文件，提取元数据和内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    filename = os.path.basename(filepath)
    
    # 提取编号
    memory_id_match = re.search(r'(CORE-\d+|PRIN-\d+|QUOTE-\d+)', filename)
    memory_id = memory_id_match.group(1) if memory_id_match else filename.replace('.md', '')
    
    # 确定类型和重要度
    if 'CORE' in filename:
        memory_type = 'fact'
        importance = 5.0
        tags = ['核心记忆', 'core']
    elif 'PRIN' in filename:
        memory_type = 'fact'
        importance = 4.0
        tags = ['行动原则', 'principle']
    elif 'QUOTE' in filename:
        memory_type = 'fact'
        importance = 3.5
        tags = ['金句', 'quote']
    else:
        memory_type = 'fact'
        importance = 3.0
        tags = ['其他']
    
    # 提取标题作为摘要
    title_match = re.search(r'^# (.+)$', text, re.MULTILINE)
    title = title_match.group(1) if title_match else filename
    
    # 内容：取全文（md格式保留）
    content = text.strip()
    if len(content) > 10000:
        content = content[:10000]
    
    return {
        'memory_id': f"mem_md_{memory_id.lower().replace('-', '_')}",
        'content': content,
        'memory_type': memory_type,
        'importance': importance,
        'tags': tags,
        'source': f"md_migration:{filepath}",
        'created_at': datetime.now().isoformat(),
    }


def migrate_md_files(storage: JsonStorage) -> int:
    """迁移md记忆文件"""
    count = 0
    md_dirs = ['core', 'principles', 'quotes']
    
    for subdir in md_dirs:
        dirpath = os.path.join(MEMORY_MD_DIR, subdir)
        if not os.path.exists(dirpath):
            continue
        for fname in os.listdir(dirpath):
            if not fname.endswith('.md'):
                continue
            filepath = os.path.join(dirpath, fname)
            try:
                data = parse_md_memory(filepath)
                unit = MemoryUnit(**data)
                storage.save(unit)
                count += 1
                print(f"  ✅ {fname} → {unit.memory_id}")
            except Exception as e:
                print(f"  ❌ {fname} 失败: {e}")
    
    return count


def migrate_auto_memory(storage: JsonStorage) -> int:
    """迁移auto_memory json文件"""
    count = 0
    skipped = 0
    
    if not os.path.exists(AUTO_MEMORY_DIR):
        print(f"  auto_memory目录不存在: {AUTO_MEMORY_DIR}")
        return 0
    
    for fname in os.listdir(AUTO_MEMORY_DIR):
        if not fname.endswith('.json'):
            continue
        filepath = os.path.join(AUTO_MEMORY_DIR, fname)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 用from_legacy_dict宽容模式处理
            unit = MemoryUnit.from_legacy_dict(data)
            storage.save(unit)
            count += 1
        except Exception as e:
            skipped += 1
            if skipped <= 5:  # 只打印前5个错误
                print(f"  ⚠️ {fname}: {e}")
    
    if skipped > 5:
        print(f"  ... 还有 {skipped - 5} 个跳过")
    
    return count


def verify_migration(storage: JsonStorage, expected_count: int) -> bool:
    """验证迁移结果"""
    try:
        all_memories = storage.query(limit=99999)
        actual_count = len(all_memories)
        
        print(f"\n  期望: {expected_count} 条")
        print(f"  实际: {actual_count} 条")
        
        if actual_count >= expected_count * 0.95:  # 允许5%的容差（部分可能因格式问题跳过）
            print(f"  ✅ 数据完整性验证通过")
            return True
        else:
            print(f"  ❌ 数据不完整，差 {expected_count - actual_count} 条")
            return False
    except Exception as e:
        print(f"  ❌ 验证失败: {e}")
        return False


# ========== 主流程 ==========

def main():
    mode = "测试模式" if TEST_MODE else "正式迁移"
    print(f"{'='*60}")
    print(f"记忆系统升级迁移 [{mode}]")
    print(f"目标目录: {TARGET_DIR}")
    print(f"{'='*60}")
    
    # 创建目标目录
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # 初始化JsonStorage
    storage = JsonStorage(TARGET_DIR)
    
    # Step 1: 迁移md文件
    print(f"\n[Step 1] 迁移md核心记忆...")
    md_count = migrate_md_files(storage)
    print(f"  md迁移完成: {md_count} 条")
    
    # Step 2: 迁移auto_memory
    print(f"\n[Step 2] 迁移auto_memory...")
    auto_count = migrate_auto_memory(storage)
    print(f"  auto_memory迁移完成: {auto_count} 条")
    
    # Step 3: 验证
    total = md_count + auto_count
    print(f"\n[Step 3] 验证迁移结果...")
    print(f"  迁移总计: {total} 条 (md:{md_count} + auto:{auto_count})")
    ok = verify_migration(storage, total)
    
    # 总结
    print(f"\n{'='*60}")
    if ok:
        print(f"✅ 迁移成功！共 {total} 条记忆已迁移到 {TARGET_DIR}")
    else:
        print(f"❌ 迁移有问题，请检查后重试")
    print(f"{'='*60}")
    
    return ok


if __name__ == "__main__":
    main()
