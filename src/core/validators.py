"""
验证工具模块

提供输入数据校验功能。
"""

from typing import Any, List, Optional, Tuple


class ValidationError(Exception):
    """验证错误异常"""
    pass


def validate_memory_content(content: Any, max_length: int = 10000) -> Tuple[bool, str]:
    """
    验证记忆内容
    
    Args:
        content: 要验证的内容
        max_length: 最大长度限制
        
    Returns:
        Tuple[bool, str]: (是否通过, 错误信息)
    """
    if content is None:
        return False, "内容不能为空"
    
    if not isinstance(content, str):
        return False, f"内容必须是字符串，当前类型: {type(content).__name__}"
    
    if len(content.strip()) == 0:
        return False, "内容不能为空字符串"
    
    if len(content) > max_length:
        return False, f"内容长度超过限制: {len(content)} > {max_length}"
    
    return True, ""


def validate_memory_type(memory_type: Any) -> Tuple[bool, str]:
    """
    验证记忆类型
    
    Args:
        memory_type: 要验证的类型
        
    Returns:
        Tuple[bool, str]: (是否通过, 错误信息)
    """
    valid_types = ["fact", "preference", "context", "task", "event"]
    
    if memory_type is None:
        return False, "类型不能为空"
    
    if not isinstance(memory_type, str):
        return False, f"类型必须是字符串，当前类型: {type(memory_type).__name__}"
    
    if memory_type not in valid_types:
        return False, f"无效的类型 '{memory_type}'，有效类型: {', '.join(valid_types)}"
    
    return True, ""


def validate_importance(importance: Any) -> Tuple[bool, str]:
    """
    验证重要度评分
    
    Args:
        importance: 要验证的评分
        
    Returns:
        Tuple[bool, str]: (是否通过, 错误信息)
    """
    if importance is None:
        return False, "重要度不能为空"
    
    if not isinstance(importance, (int, float)):
        return False, f"重要度必须是数字，当前类型: {type(importance).__name__}"
    
    if not (1.0 <= float(importance) <= 5.0):
        return False, f"重要度必须在1.0-5.0之间，当前值: {importance}"
    
    return True, ""


def validate_memory_unit(data: dict) -> Tuple[bool, List[str]]:
    """
    验证完整的MemoryUnit数据
    
    Args:
        data: MemoryUnit数据字典
        
    Returns:
        Tuple[bool, List[str]]: (是否通过, 错误信息列表)
    """
    errors = []
    
    # 检查必填字段
    required_fields = ["content", "memory_type", "importance"]
    for field in required_fields:
        if field not in data:
            errors.append(f"缺少必填字段: {field}")
    
    if errors:
        return False, errors
    
    # 验证各字段
    validators = [
        ("content", validate_memory_content),
        ("memory_type", validate_memory_type),
        ("importance", validate_importance),
    ]
    
    for field, validator in validators:
        if field in data:
            is_valid, error_msg = validator(data[field])
            if not is_valid:
                errors.append(f"字段 '{field}': {error_msg}")
    
    return len(errors) == 0, errors


if __name__ == "__main__":
    # 简单测试
    print("验证工具测试:")
    
    # 测试内容验证
    print("\n1. 内容验证:")
    cases = [
        ("正常内容", True),
        ("", False),
        (None, False),
        ("x" * 10001, False),
    ]
    for content, expected in cases:
        is_valid, error = validate_memory_content(content)
        status = "✅" if is_valid == expected else "❌"
        print(f"  {status} '{str(content)[:20]}...' -> {is_valid}")
    
    # 测试类型验证
    print("\n2. 类型验证:")
    for mtype in ["fact", "preference", "invalid", None]:
        is_valid, error = validate_memory_type(mtype)
        status = "✅" if is_valid else "❌"
        print(f"  {status} '{mtype}' -> {is_valid}")
    
    # 测试完整验证
    print("\n3. 完整MemoryUnit验证:")
    valid_data = {
        "content": "这是一条测试记忆",
        "memory_type": "fact",
        "importance": 4.5
    }
    is_valid, errors = validate_memory_unit(valid_data)
    print(f"  ✅ 有效数据: {is_valid}")
    
    invalid_data = {
        "content": "",
        "memory_type": "invalid_type"
    }
    is_valid, errors = validate_memory_unit(invalid_data)
    print(f"  ❌ 无效数据: {is_valid}, 错误: {errors}")
