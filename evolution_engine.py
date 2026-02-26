#!/usr/bin/env python
"""
安仔自我进化引擎

功能：
1. 任务结束自动反思
2. 成功/失败标记
3. 提取经验和教训
4. 更新做事框架
"""

import sys
sys.path.insert(0, 'src')

from auto_memory_bridge import remember, recall
from datetime import datetime


class EvolutionEngine:
    """
    自我进化引擎
    
    实现：记忆 → 反思 → 框架 → 进化
    """
    
    def __init__(self):
        self.reflections = []
    
    def on_task_complete(self, task: str, result: str, success: bool, feedback: str = ""):
        """
        任务完成时调用
        
        Args:
            task: 任务描述
            result: 执行结果
            success: 是否成功
            feedback: 安哥反馈
        """
        # 1. 记录事件
        event_type = 'success' if success else 'failure'
        remember(
            content=f'任务：{task}\n结果：{result}\n反馈：{feedback}',
            memory_type='event',
            importance=4.5 if success else 5.0,  # 失败更重要
            tags=['任务', event_type, '复盘']
        )
        
        # 2. 立即反思
        reflection = self._reflect(task, result, success, feedback)
        
        # 3. 提取框架
        if success:
            self._extract_success_pattern(task, reflection)
        else:
            self._extract_lesson(task, reflection)
        
        return reflection
    
    def _reflect(self, task: str, result: str, success: bool, feedback: str) -> dict:
        """反思分析"""
        reflection = {
            'task': task,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'why_success': '',
            'why_failure': '',
            'improvement': ''
        }
        
        if success:
            reflection['why_success'] = self._analyze_success(task, result, feedback)
        else:
            reflection['why_failure'] = self._analyze_failure(task, result, feedback)
            reflection['improvement'] = self._suggest_improvement(task, result)
        
        # 保存反思
        remember(
            content=f'复盘：{task}\n成功：{success}\n原因：{reflection.get("why_success") or reflection.get("why_failure")}\n改进：{reflection.get("improvement", "")}',
            memory_type='context',
            importance=4.5,
            tags=['复盘', '反思', '进化']
        )
        
        return reflection
    
    def _analyze_success(self, task: str, result: str, feedback: str) -> str:
        """分析成功原因"""
        # 简单规则，后续可扩展AI分析
        reasons = []
        
        if '清晰' in feedback or '准确' in feedback:
            reasons.append('理解准确')
        if '快' in feedback or '及时' in feedback:
            reasons.append('响应迅速')
        if '完整' in feedback:
            reasons.append('执行完整')
        
        return '，'.join(reasons) if reasons else '执行到位'
    
    def _analyze_failure(self, task: str, result: str, feedback: str) -> str:
        """分析失败原因"""
        reasons = []
        
        if '不理解' in feedback or '错了' in feedback:
            reasons.append('理解偏差')
        if '慢' in feedback or '超时' in feedback:
            reasons.append('执行缓慢')
        if '不完整' in feedback:
            reasons.append('执行不完整')
        if '报错' in result or '失败' in result:
            reasons.append('技术故障')
        
        return '，'.join(reasons) if reasons else '需要改进'
    
    def _suggest_improvement(self, task: str, result: str) -> str:
        """建议改进方案"""
        # 检索类似任务的历史成功经验
        similar = recall(task[:10], top_k=3)
        
        if similar:
            return f'参考成功案例：{similar[0].get("content", "")[:30]}...'
        
        return '需要更多实践总结'
    
    def _extract_success_pattern(self, task: str, reflection: dict):
        """提取成功模式"""
        pattern = f'成功模式：{task[:20]}... → {reflection.get("why_success", "")}'
        
        remember(
            content=pattern,
            memory_type='fact',
            importance=4.0,
            tags=['成功模式', '最佳实践', '框架']
        )
    
    def _extract_lesson(self, task: str, reflection: dict):
        """提取教训"""
        lesson = f'教训：{task[:20]}... → 避免：{reflection.get("why_failure", "")}'
        
        remember(
            content=lesson,
            memory_type='fact',
            importance=5.0,  # 教训更重要
            tags=['教训', '避坑', '框架']
        )
    
    def get_framework(self, task_type: str) -> list:
        """
        获取某类任务的做事框架
        
        Args:
            task_type: 任务类型关键词
            
        Returns:
            框架列表
        """
        # 检索成功模式和教训
        patterns = recall(task_type, top_k=5)
        
        framework = {
            'best_practices': [],
            'lessons': [],
            'sop': []
        }
        
        for p in patterns:
            content = p.get('content', '')
            if '成功模式' in content:
                framework['best_practices'].append(content)
            elif '教训' in content:
                framework['lessons'].append(content)
        
        return framework
    
    def generate_report(self) -> str:
        """生成进化报告"""
        # 统计成功/失败
        all_events = recall('任务', top_k=50)
        
        success_count = sum(1 for e in all_events if 'success' in str(e.get('tags', [])))
        failure_count = sum(1 for e in all_events if 'failure' in str(e.get('tags', [])))
        
        # 获取框架
        patterns = recall('成功模式', top_k=5)
        lessons = recall('教训', top_k=5)
        
        total = success_count + failure_count
        success_rate = f"{success_count/total*100:.1f}%" if total > 0 else "N/A"
        
        report = f"""
📊 安仔自我进化报告
{'=' * 60}

任务统计：
  成功：{success_count} 次
  失败：{failure_count} 次
  成功率：{success_rate}

成功模式（{len(patterns)} 条）：
"""
        for i, p in enumerate(patterns[:3], 1):
            report += f"  {i}. {p.get('content', '')[:50]}...\n"
        
        report += f"\n教训总结（{len(lessons)} 条）：\n"
        for i, l in enumerate(lessons[:3], 1):
            report += f"  {i}. {l.get('content', '')[:50]}...\n"
        
        report += f"\n{'=' * 60}"
        
        return report


# 全局实例
_engine = None

def get_engine():
    """获取进化引擎实例"""
    global _engine
    if _engine is None:
        _engine = EvolutionEngine()
    return _engine


def on_complete(task: str, result: str, success: bool, feedback: str = ""):
    """便捷函数：任务完成"""
    return get_engine().on_task_complete(task, result, success, feedback)


def get_report():
    """便捷函数：获取报告"""
    return get_engine().generate_report()


if __name__ == "__main__":
    print("🧠 安仔自我进化引擎")
    print("=" * 60)
    
    # 模拟任务完成
    engine = EvolutionEngine()
    
    # 成功案例
    engine.on_task_complete(
        task="执行记忆系统启动",
        result="启动成功，加载10条记忆",
        success=True,
        feedback="清晰准确，执行完整"
    )
    
    # 失败案例
    engine.on_task_complete(
        task="修复numpy依赖问题",
        result="安装失败，版本冲突",
        success=False,
        feedback="需要更多时间解决"
    )
    
    print()
    print(engine.generate_report())
