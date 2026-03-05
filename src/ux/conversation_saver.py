"""
对话可靠保存器

整合三重保障机制，确保对话不丢失。
内部组合AutoTrigger（判断）+ 自己负责（执行）。
"""

import time
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 结束信号关键词
END_SIGNAL_KEYWORDS = [
    # 明确结束
    "保存", "结束", "下次见", "先这样", "就到这", "收工",
    "今天先到这", "拜拜", "再见", "晚安", "早安",
    # 暗示结束
    "辛苦了", "谢谢安仔", "好的就这样", "没别的了",
    # 英文
    "bye", "see you", "that's all", "done"
]


@dataclass
class SaveResult:
    """保存结果"""
    saved: bool                    # 是否执行了保存
    save_type: str                 # "realtime" / "periodic" / "end_signal" / "manual"
    file_path: Optional[str]       # 保存的文件路径
    memory_extracted: int          # 提取的记忆要点数量
    message: str                   # 描述信息


class ConversationSaver:
    """
    对话可靠保存器
    
    整合三重保障机制，确保对话不丢失。
    内部组合AutoTrigger（判断）+ 自己负责（执行）。
    """
    
    def __init__(
        self,
        save_dir: str = "D:/AnZai_JieYue/duihua",
        auto_save_interval: int = 600,  # 10分钟，单位秒
        idle_timeout: int = 900,         # 15分钟无消息视为上一段结束，单位秒
    ):
        """
        初始化
        
        内部创建：
        - self._trigger = AutoTrigger()  # 组合使用，不修改
        - self._message_buffer = []       # 对话缓冲区
        - self._last_save_time = time.time()
        - self._last_message_time = None
        - self._session_id = f"conv-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        """
        # 导入AutoTrigger（避免循环导入）
        try:
            from ux.auto_trigger import AutoTrigger, TriggerDecision
            self._trigger = AutoTrigger()
            self._TriggerDecision = TriggerDecision
        except ImportError:
            try:
                from src.ux.auto_trigger import AutoTrigger, TriggerDecision
                self._trigger = AutoTrigger()
                self._TriggerDecision = TriggerDecision
            except Exception as e:
                logger.warning(f"AutoTrigger导入失败: {e}")
                self._trigger = None
                self._TriggerDecision = None
        
        # 保存配置
        self._save_dir = Path(save_dir)
        self._save_dir.mkdir(parents=True, exist_ok=True)
        self._auto_save_interval = auto_save_interval
        self._idle_timeout = idle_timeout
        
        # 状态管理
        self._message_buffer: List[Dict[str, Any]] = []
        self._last_save_time = time.time()
        self._last_message_time: Optional[float] = None
        self._session_start_time = time.time()
        self._session_id = f"conv-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self._save_count = 0
        self._memory_points: List[Dict[str, Any]] = []
        
        logger.info(f"ConversationSaver初始化: session_id={self._session_id}, save_dir={save_dir}")
    
    def on_message(self, role: str, content: str) -> SaveResult:
        """
        处理每条消息（核心入口）
        
        执行顺序：
        1. 检查idle超时：距上条消息>15分钟？→ 先保存上段对话，开新会话
        2. 追加消息到缓冲区
        3. 检查定时保存：距上次保存>10分钟？→ 保存
        4. 检查结束信号：内容匹配结束关键词？→ 保存
        5. 调用AutoTrigger.analyze()：置信度>=0.6？→ 标记为记忆要点（不单独保存文件）
        6. 返回SaveResult
        
        Args:
            role: "user" 或 "assistant"
            content: 消息内容
            
        Returns:
            SaveResult
        """
        now = time.time()
        result = SaveResult(
            saved=False,
            save_type="none",
            file_path=None,
            memory_extracted=0,
            message=""
        )
        
        try:
            # 1. 检查idle超时
            if self._last_message_time and (now - self._last_message_time > self._idle_timeout):
                logger.info(f"检测到idle超时，保存上一段对话")
                self._save_conversation()
                self._start_new_session()
                result.message = f"检测到{int(self._idle_timeout/60)}分钟无消息，已保存上一段对话"
            
            # 2. 追加消息到缓冲区
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            self._message_buffer.append(message)
            self._last_message_time = now
            
            # 3. 调用AutoTrigger分析，提取记忆要点
            memory_extracted = 0
            if role == "user" and self._trigger:
                decision = self._trigger.should_save(content)
                if decision.should_save and decision.confidence >= 0.6:
                    self._memory_points.append({
                        "content": content,
                        "confidence": decision.confidence,
                        "reason": decision.reason,
                        "source_message_index": len(self._message_buffer) - 1
                    })
                    memory_extracted = 1
                    result.memory_extracted = memory_extracted
            
            # 4. 检查定时保存
            if now - self._last_save_time >= self._auto_save_interval:
                logger.info(f"检测到定时保存（{int(self._auto_save_interval/60)}分钟）")
                file_path = self._save_conversation()
                result.saved = True
                result.save_type = "periodic"
                result.file_path = file_path
                result.message = f"定时保存（{int(self._auto_save_interval/60)}分钟）"
                return result
            
            # 5. 检查结束信号
            if role == "user" and self._check_end_signal(content):
                logger.info(f"检测到结束信号，保存对话")
                file_path = self._save_conversation()
                result.saved = True
                result.save_type = "end_signal"
                result.file_path = file_path
                result.message = "检测到结束信号，已保存对话"
                return result
            
            # 如果没有保存，但有记忆提取
            if memory_extracted > 0:
                result.message = f"已提取{memory_extracted}条记忆要点"
            
            return result
            
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            result.message = f"处理消息时出错: {str(e)}"
            return result
    
    def force_save(self) -> str:
        """
        强制保存当前对话（手动触发）
        
        Returns:
            保存的文件路径
        """
        logger.info("强制保存对话")
        return self._save_conversation()
    
    def get_session_summary(self) -> dict:
        """
        获取当前会话摘要
        
        Returns:
            {
                "session_id": str,
                "message_count": int,
                "duration_seconds": float,
                "save_count": int,
                "memory_points_count": int,
                "last_save_time": str
            }
        """
        now = time.time()
        return {
            "session_id": self._session_id,
            "message_count": len(self._message_buffer),
            "duration_seconds": now - self._session_start_time,
            "save_count": self._save_count,
            "memory_points_count": len(self._memory_points),
            "last_save_time": datetime.fromtimestamp(self._last_save_time).isoformat() if self._last_save_time else None
        }
    
    def _save_conversation(self) -> str:
        """
        保存完整对话记录到JSON
        
        写入路径：{save_dir}/{session_id}.json
        格式：兼容现有conversation-auto-saver格式
        写入后更新self._last_save_time
        
        Returns:
            文件路径
        """
        try:
            # 构建对话数据
            conversation_data = {
                "conversation_id": self._session_id,
                "title": f"对话 {datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
                "created_at": datetime.fromtimestamp(self._session_start_time).isoformat(),
                "updated_at": datetime.now().isoformat(),
                "participants": ["安哥(human)", "安仔(assistant)"],
                "metadata": {
                    "session": "R07",
                    "type": "数字分身训练",
                    "auto_saved": True,
                    "save_count": self._save_count + 1,
                    "memory_extracted": len(self._memory_points)
                },
                "messages": self._message_buffer.copy(),
                "extracted_memories": self._memory_points.copy()
            }
            
            # 保存文件
            file_path = self._save_dir / f"{self._session_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            # 更新状态
            self._save_count += 1
            self._last_save_time = time.time()
            
            logger.info(f"对话已保存: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"保存对话失败: {e}")
            raise
    
    def _extract_memory_points(self) -> list:
        """
        从缓冲区提取记忆要点
        
        规则：
        1. 遍历所有user消息
        2. AutoTrigger.analyze()逐条分析
        3. 置信度>=0.6的提取为要点
        4. 要点只记录在JSON的extracted_memories字段，不写入核心记忆
        
        Returns:
            [{"content": str, "confidence": float, "reason": str, "source_message_index": int}]
        """
        points = []
        if not self._trigger:
            return points
        
        for i, msg in enumerate(self._message_buffer):
            if msg["role"] != "user":
                continue
            
            decision = self._trigger.should_save(msg["content"])
            if decision.should_save and decision.confidence >= 0.6:
                points.append({
                    "content": msg["content"],
                    "confidence": decision.confidence,
                    "reason": decision.reason,
                    "source_message_index": i
                })
        
        return points
    
    def _check_end_signal(self, content: str) -> bool:
        """
        检测对话结束信号
        
        匹配END_SIGNAL_KEYWORDS列表，返回是否命中
        """
        content_lower = content.lower()
        for keyword in END_SIGNAL_KEYWORDS:
            if keyword in content_lower:
                return True
        return False
    
    def _start_new_session(self):
        """
        开始新会话
        
        重置缓冲区、session_id、计时器
        """
        logger.info("开始新会话")
        self._message_buffer = []
        self._memory_points = []
        self._session_start_time = time.time()
        self._session_id = f"conv-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self._last_save_time = time.time()
