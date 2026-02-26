# M3 自动优化模块使用指南

**版本**: v3.0  
**更新日期**: 2026-02-24  
**状态**: ✅ 已完成

---

## 概述

M3自动优化模块提供记忆系统的自动性能优化功能：

- **性能监控**: 实时监控检索性能，检测慢查询和错误
- **缓存管理**: 智能缓存策略，提高访问效率
- **索引优化**: 自动索引维护，保持检索效率
- **自动调优**: 根据性能指标自动调整参数

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     AutoOptimizer                           │
│                    (自动优化器)                              │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
      ┌────────▼────────┐          ┌──────────▼──────────┐
      │PerformanceMonitor│         │   IndexOptimizer    │
      │   (性能监控)     │          │    (索引优化)        │
      └────────┬────────┘          └──────────┬──────────┘
               │                              │
      ┌────────▼────────┐          ┌──────────▼──────────┐
      │  CacheManager   │          │   Storage Backend   │
      │   (缓存管理)     │          │    (存储后端)        │
      └─────────────────┘          └─────────────────────┘
```

---

## 快速开始

### 1. 基础使用

```python
from optimization import AutoOptimizer

# 创建自动优化器
optimizer = AutoOptimizer(
    storage=storage,  # 存储后端
    enable_monitoring=True,
    enable_auto_optimize=True,
    optimize_interval_minutes=60
)

# 启动自动优化
optimizer.start()

# 使用监控功能
with optimizer.record_operation("search"):
    results = vector_search.search("查询")

# 获取优化报告
report = optimizer.get_optimization_report()
print(report)

# 停止自动优化
optimizer.stop()
```

### 2. 性能监控

```python
from optimization import PerformanceMonitor

# 创建监控器
monitor = PerformanceMonitor(
    slow_threshold_ms=100.0,  # 慢查询阈值
    max_history=1000          # 最大历史记录
)

# 记录操作性能
with monitor.record("search"):
    results = vector_search.search("查询")

# 获取统计
stats = monitor.get_stats("search")
print(f"平均延迟: {stats['avg_latency_ms']:.2f}ms")
print(f"P95延迟: {stats['p95_latency_ms']:.2f}ms")
print(f"错误率: {stats['error_rate']*100:.1f}%")

# 获取慢查询
slow_queries = monitor.get_slow_queries(limit=10)
for q in slow_queries:
    print(f"{q.operation}: {q.duration_ms:.2f}ms")
```

### 3. 缓存管理

```python
from optimization import CacheManager, MultiLevelCache

# 创建缓存
 cache = CacheManager(
    max_size=1000,           # 最大条目数
    ttl_seconds=3600,        # TTL（秒）
    max_memory_mb=100.0      # 最大内存
)

# 设置缓存
cache.set("key1", value)

# 获取缓存
value = cache.get("key1")

# 多级缓存
multi_cache = MultiLevelCache(l1_size=100, l2_size=1000)
multi_cache.set("key1", value)
value = multi_cache.get("key1")  # 先查L1，再查L2

# 获取统计
stats = cache.get_stats()
print(f"命中率: {stats['hit_rate']:.2%}")
print(f"大小: {stats['size']}/{stats['max_size']}")
```

### 4. 索引优化

```python
from optimization import IndexOptimizer

# 创建优化器
optimizer = IndexOptimizer(storage)

# 分析索引
stats = optimizer.analyze()
print(f"文档数: {stats.total_documents}")
print(f"碎片率: {stats.fragmentation_ratio:.2%}")

# 查找重复
 duplicates = optimizer.find_duplicates(similarity_threshold=0.95)
print(f"发现 {len(duplicates)} 对重复")

# 执行优化
result = optimizer.optimize()
print(f"移除重复: {result['duplicates_removed']}")
print(f"归档冷数据: {result['cold_data_archived']}")

# 获取建议
for rec in optimizer.get_recommendations():
    print(f"建议: {rec}")
```

---

## API参考

### AutoOptimizer

自动优化器，整合所有优化功能。

#### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `start()` | - | - | 启动自动优化 |
| `stop()` | - | - | 停止自动优化 |
| `record_operation()` | operation, metadata | context | 记录操作 |
| `get_performance_stats()` | - | dict | 获取性能统计 |
| `get_cache_stats()` | - | dict | 获取缓存统计 |
| `get_optimization_report()` | - | str | 获取优化报告 |
| `cache_get/set/delete()` | ... | ... | 缓存操作 |

### PerformanceMonitor

性能监控器，监控操作性能。

#### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `record()` | operation, metadata | context | 上下文记录 |
| `record_manual()` | operation, duration_ms, ... | - | 手动记录 |
| `get_stats()` | operation, time_window | dict | 获取统计 |
| `get_slow_queries()` | limit, operation | list | 获取慢查询 |
| `get_errors()` | limit, operation | list | 获取错误 |
| `get_summary()` | - | str | 获取摘要 |

#### 统计指标

| 指标 | 说明 |
|------|------|
| `count` | 调用次数 |
| `avg_latency_ms` | 平均延迟 |
| `p95_latency_ms` | P95延迟 |
| `p99_latency_ms` | P99延迟 |
| `error_rate` | 错误率 |
| `hit_rate` | 命中率（缓存） |

### CacheManager

缓存管理器，提供智能缓存。

#### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get()` | key | value/None | 获取缓存 |
| `set()` | key, value, ttl_seconds | bool | 设置缓存 |
| `delete()` | key | bool | 删除缓存 |
| `clear()` | - | - | 清空缓存 |
| `get_stats()` | - | dict | 获取统计 |
| `get_popular_keys()` | top_n | list | 获取热门键 |
| `cleanup_expired()` | - | int | 清理过期 |

#### 缓存策略

- **LRU**: 最近最少使用淘汰
- **TTL**: 时间过期
- **Size Limit**: 大小限制
- **Memory Limit**: 内存限制

### IndexOptimizer

索引优化器，维护索引健康。

#### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `analyze()` | - | IndexStats | 分析索引 |
| `find_duplicates()` | similarity_threshold | list | 查找重复 |
| `find_cold_data()` | days | list | 查找冷数据 |
| `optimize()` | - | dict | 执行优化 |
| `get_recommendations()` | - | list | 获取建议 |

---

## 配置选项

### AutoOptimizer配置

```python
AutoOptimizer(
    storage=storage,                    # 存储后端
    enable_monitoring=True,             # 启用监控
    enable_auto_optimize=True,          # 启用自动优化
    optimize_interval_minutes=60,       # 优化间隔
    slow_query_threshold_ms=100.0,      # 慢查询阈值
    cache_size=1000                     # 缓存大小
)
```

### PerformanceMonitor配置

```python
PerformanceMonitor(
    max_history=1000,                   # 最大历史记录
    slow_threshold_ms=100.0,            # 慢查询阈值
    alert_callback=on_alert             # 告警回调
)
```

### CacheManager配置

```python
CacheManager(
    max_size=1000,                      # 最大条目数
    ttl_seconds=3600,                   # TTL
    max_memory_mb=100.0,                # 最大内存
    eviction_callback=on_evict          # 淘汰回调
)
```

---

## 性能优化建议

### 1. 监控关键指标

```python
# 定期检查性能
stats = monitor.get_stats()

# 关注指标
if stats['p95_latency_ms'] > 200:
    logger.warning("P95延迟过高，需要优化")

if stats['error_rate'] > 0.01:
    logger.error("错误率过高，需要排查")
```

### 2. 缓存策略

```python
# 高频数据使用短TTL
cache.set("hot_data", value, ttl_seconds=300)

# 低频数据使用长TTL
cache.set("cold_data", value, ttl_seconds=3600)

# 大数据使用内存限制
cache = CacheManager(max_memory_mb=500.0)
```

### 3. 索引维护

```python
# 定期执行优化
optimizer.optimize()

# 处理重复数据
duplicates = optimizer.find_duplicates()
if duplicates:
    optimizer.optimize()

# 归档冷数据
cold_ids = optimizer.find_cold_data(days=90)
```

---

## 测试

### 运行测试

```bash
# 性能监控测试
python -m pytest tests/test_performance_monitor.py -v

# 缓存管理测试
python -m pytest tests/test_cache_manager.py -v

# 集成测试
python -m pytest tests/integration/test_m3_optimization_integration.py -v
```

### 测试结果

| 模块 | 测试数 | 状态 |
|------|--------|------|
| 性能监控器 | 10 | ✅ |
| 缓存管理器 | 12 | ✅ |
| M3集成测试 | 17 | ✅ |
| **总计** | **39** | **✅** |

---

## 故障排除

### 问题1: 缓存命中率低

**原因**: 
- TTL设置过短
- 缓存容量不足
- 访问模式不规律

**解决**:
```python
# 调整TTL
cache = CacheManager(ttl_seconds=7200)  # 增加TTL

# 增加容量
cache = CacheManager(max_size=5000)

# 使用多级缓存
multi_cache = MultiLevelCache(l1_size=100, l2_size=1000)
```

### 问题2: 性能监控数据丢失

**原因**: 历史记录超过max_history

**解决**:
```python
# 增加历史记录容量
monitor = PerformanceMonitor(max_history=10000)

# 定期导出数据
stats = monitor.get_stats()
# 保存到文件或数据库
```

### 问题3: 自动优化影响性能

**原因**: 优化间隔过短

**解决**:
```python
# 调整优化间隔
optimizer = AutoOptimizer(
    optimize_interval_minutes=180  # 3小时
)
```

---

## 更新日志

### 2026-02-24
- ✅ 完成性能监控器
- ✅ 完成缓存管理器
- ✅ 完成索引优化器
- ✅ 完成自动优化器
- ✅ 完成39个测试用例
- ✅ 完成使用文档

---

## 下一步

- M4: 四层完善（核心层+检索层+存储层+傻瓜层集成）
- M5: 系统集成测试
