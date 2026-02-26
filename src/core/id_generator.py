"""
ID生成器模块

为MemoryUnit生成唯一标识符。
"""

import secrets
import string
try:
    from .timestamp_utils import get_timestamp_for_id
except ImportError:
    from timestamp_utils import get_timestamp_for_id


def generate_memory_id() -> str:
    """
    生成MemoryUnit的唯一标识符
    
    格式: mem_{timestamp}_{random}
    例如: mem_20260223105034_a1b2c3d4
    
    Returns:
        str: 唯一标识符
    """
    timestamp = get_timestamp_for_id()
    # 生成8位随机字符串（小写字母+数字）
    random_part = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return f"mem_{timestamp}_{random_part}"


def validate_memory_id(memory_id: str) -> bool:
    """
    验证MemoryUnit ID格式是否正确
    
    Args:
        memory_id: 要验证的ID字符串
        
    Returns:
        bool: 格式正确返回True，否则返回False
    """
    if not isinstance(memory_id, str):
        return False
    
    parts = memory_id.split('_')
    if len(parts) != 3 or parts[0] != 'mem':
        return False
    
    # 验证时间戳部分（14位数字）
    if not (len(parts[1]) == 14 and parts[1].isdigit()):
        return False
    
    # 验证随机部分（8位小写字母+数字）
    if not (len(parts[2]) == 8 and all(c in string.ascii_lowercase + string.digits for c in parts[2])):
        return False
    
    return True


if __name__ == "__main__":
    # 简单测试
    ids = [generate_memory_id() for _ in range(5)]
    print("生成的ID:")
    for mid in ids:
        print(f"  {mid} - 格式验证: {validate_memory_id(mid)}")
    
    # 唯一性测试
    print(f"\n生成10000个ID，唯一性检查...")
    id_set = set(generate_memory_id() for _ in range(10000))
    print(f"唯一ID数量: {len(id_set)} / 10000")
    print(f"唯一性: {'✅ 通过' if len(id_set) == 10000 else '❌ 有重复'}")
