# -*- coding: utf-8 -*-
"""T2验收测试 - 10项验收清单逐项检查"""
import sys
import os
import time
import tempfile
import json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'D:\projects\memory_system_v3\src')

from ux.conversation_saver import ConversationSaver, SaveResult, END_SIGNAL_KEYWORDS

results = []

def check(name, passed, detail=""):
    tag = "PASS" if passed else "FAIL"
    results.append((name, passed, detail))
    print(f"  [{tag}] {name}" + (f" - {detail}" if detail else ""))

print("=" * 60)
print("T2 验收测试 - 10项验收清单")
print("=" * 60)

# --- 验收项1: 每条消息调用on_message()不报错，模拟10轮对话 ---
print("\n[1] 每条消息调用on_message()不报错")
td1 = tempfile.mkdtemp()
saver1 = ConversationSaver(save_dir=td1, auto_save_interval=600, idle_timeout=900)
msgs = []
for i in range(10):
    msgs.append(("user", f"用户消息第{i+1}轮"))
    msgs.append(("assistant", f"助手回复第{i+1}轮"))
error_count = 0
for role, content in msgs:
    try:
        r = saver1.on_message(role, content)
        assert isinstance(r, SaveResult)
    except Exception as e:
        error_count += 1
check("10轮对话(20条消息)不报错", error_count == 0, f"错误数={error_count}")

# --- 验收项2: 包含"记住"关键词时自动提取记忆 ---
print("\n[2] 包含关键词时自动提取记忆")
td2 = tempfile.mkdtemp()
saver2 = ConversationSaver(save_dir=td2, auto_save_interval=600, idle_timeout=900)
r2 = saver2.on_message("user", "记住，我喜欢喝咖啡")
summary2 = saver2.get_session_summary()
check("关键词触发记忆提取", summary2["memory_points_count"] >= 1, f"提取数={summary2['memory_points_count']}")

# --- 验收项3: 10分钟自动保存(短间隔测试) ---
print("\n[3] 定时自动保存")
td3 = tempfile.mkdtemp()
saver3 = ConversationSaver(save_dir=td3, auto_save_interval=1, idle_timeout=900)
saver3.on_message("user", "test periodic")
time.sleep(1.2)
r3 = saver3.on_message("user", "trigger periodic save")
check("定时保存触发", r3.saved and r3.save_type == "periodic", f"saved={r3.saved}, type={r3.save_type}")

# --- 验收项4: 检测到结束信号时自动保存 ---
print("\n[4] 结束信号检测")
td4 = tempfile.mkdtemp()
saver4 = ConversationSaver(save_dir=td4, auto_save_interval=600, idle_timeout=900)
saver4.on_message("user", "hello")
r4 = saver4.on_message("user", "先这样")
check("结束信号保存", r4.saved and r4.save_type == "end_signal", f"saved={r4.saved}, type={r4.save_type}")

# --- 验收项5: force_save()手动保存正常 ---
print("\n[5] force_save()手动保存")
td5 = tempfile.mkdtemp()
saver5 = ConversationSaver(save_dir=td5, auto_save_interval=600, idle_timeout=900)
saver5.on_message("user", "test force save")
path5 = saver5.force_save()
check("force_save正常", os.path.exists(path5), f"path={path5}")

# --- 验收项6: 保存的JSON格式与现有兼容 ---
print("\n[6] JSON格式兼容性")
with open(path5, 'r', encoding='utf-8') as f:
    data = json.load(f)
required_fields = ["conversation_id", "title", "created_at", "updated_at", "participants", "metadata", "messages"]
missing = [k for k in required_fields if k not in data]
has_extracted = "extracted_memories" in data
check("JSON必需字段完整", len(missing) == 0, f"缺失={missing}")
check("新增extracted_memories字段", has_extracted)

# --- 验收项7: 15分钟无消息自动保存(短间隔测试) ---
print("\n[7] idle超时自动保存")
td7 = tempfile.mkdtemp()
saver7 = ConversationSaver(save_dir=td7, auto_save_interval=600, idle_timeout=2)
saver7.on_message("user", "first segment")
time.sleep(2.5)
r7 = saver7.on_message("user", "new segment after idle")
check("idle超时保存", "已保存上一段对话" in r7.message or r7.saved, f"msg={r7.message}")

# --- 验收项8: 保存失败时不影响对话继续 ---
print("\n[8] 保存失败不影响对话")
# 注意：__init__中mkdir在磁盘不存在时会崩，这是一个缺陷
# 但on_message内部有try-except保护，保存失败时返回SaveResult不崩
# 这里测试on_message层面的异常保护
td8 = tempfile.mkdtemp()
saver8 = ConversationSaver(save_dir=td8, auto_save_interval=600, idle_timeout=900)
# 删除目录模拟保存失败
import shutil
shutil.rmtree(td8)
r8 = saver8.on_message("user", "先这样")  # 触发结束信号保存，但目录已删
check("保存失败不崩溃", isinstance(r8, SaveResult), f"saved={r8.saved}, msg={r8.message}")

# --- 验收项9: get_session_summary()返回正确统计 ---
print("\n[9] get_session_summary()正确性")
td9 = tempfile.mkdtemp()
saver9 = ConversationSaver(save_dir=td9, auto_save_interval=600, idle_timeout=900)
saver9.on_message("user", "msg1")
saver9.on_message("assistant", "msg2")
saver9.on_message("user", "记住这个很重要")
s9 = saver9.get_session_summary()
check("消息计数正确", s9["message_count"] == 3, f"count={s9['message_count']}")
check("session_id存在", "session_id" in s9 and s9["session_id"].startswith("conv-"))

# --- 验收项10: 对话记录保存到正确目录 ---
print("\n[10] 保存到正确目录")
target_dir = r"D:\AnZai_JieYue\duihua"
saver10 = ConversationSaver(save_dir=target_dir, auto_save_interval=600, idle_timeout=900)
saver10.on_message("user", "acceptance test")
path10 = saver10.force_save()
check("保存到duihua目录", path10.startswith(target_dir), f"path={path10}")
# 清理测试文件
if os.path.exists(path10):
    os.remove(path10)
    print(f"  (已清理测试文件)")

# --- 汇总 ---
print("\n" + "=" * 60)
print("验收汇总")
print("=" * 60)
passed = sum(1 for _, p, _ in results if p)
total = len(results)
for name, p, detail in results:
    tag = "PASS" if p else "FAIL"
    print(f"  [{tag}] {name}")
print(f"\n总计: {passed}/{total} 通过")
if passed == total:
    print("结论: 全部通过")
else:
    print("结论: 存在未通过项")
