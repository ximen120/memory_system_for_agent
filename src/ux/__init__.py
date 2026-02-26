"""
傻瓜层（UX层）模块

提供全自动、零配置、自然语言交互的用户体验。
"""

from .auto_trigger import AutoTrigger, TriggerDecision

try:
    from .nlp_parser import NLPParser
    __all__ = [
        "AutoTrigger",
        "TriggerDecision",
        "NLPParser",
    ]
except ImportError:
    __all__ = [
        "AutoTrigger",
        "TriggerDecision",
    ]
