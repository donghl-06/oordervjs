#!/usr/bin/env python3
"""第0步验证脚本：orderid 对齐 / 引擎调用耗时 / 映射构建开销
运行：cd ordervis_server && ../.venv/bin/python verify_step0.py
"""
import sys, time, tracemalloc, json
sys.path.insert(0, '/home/donghuale/project2-test')
sys.path.insert(0, '/home/donghuale/project2-test/ordervis_server')
sys.path.append('/home/donghuale/venv_adata/lib/python3.11/site-packages')

import pandas as pd
import lib.pywangcai_orderbook as wc

SYM, DATE = '000027.SZ', '2025-08-01'

print('=' * 60)
print(f'验证标的: {SYM} {DATE}')
print('=' * 60)

# ---- 1. 引擎初始化耗时 ----
t0 = time.time()
viz = wc.TradingVisualizer(SYM, DATE, './data/', False)
viz.run()
print(f'\n[1] 引擎初始化(run)耗时: {time.time()-t0:.2f}s')
print(f'    总快照数: {viz.get_total_snapshots()}, 总变化数: {viz.get_total_changes()}')
print(f'    时间范围: {viz.get_time_range()}')

# ---- 2. 快照结构探查 + order_id 收集 ----
snap = viz.query_by_time(DATE, '10:00:00.000')
print(f'\n[2] 快照结构 keys: {list(snap.keys()) if isinstance(snap, dict) else type(snap)}')
levels = snap.get('levels', snap)
print(f'    levels keys: {list(levels.keys())}')

def collect_ids(snapshot):
    ids = set()
    lv = snapshot.get('levels', snapshot)
    for side_key, lvls in lv.items() if isinstance(lv, dict) else []:
        if not isinstance(lvls, (list, dict)):
            continue
        items = lvls.values() if isinstance(lvls, dict) else lvls
        for level in items:
            if not isinstance(level, dict):
                continue
            for o in level.get('orders', []):
                oid = o.get('order_id')
                if oid is not None:
                    ids.add(int(oid))
    return ids

sample_ids = collect_ids(snap)
print(f'    10:00 快照订单数: {len(sample_ids)}, 示例: {sorted(sample_ids)[:5]}')
one_level = None
lv = snap.get('levels', snap)
for side_key, lvls in (lv.items() if isinstance(lv, dict) else []):
    items = lvls.values() if isinstance(lvls, dict) else lvls
    for level in items:
        if isinstance(level, dict) and level.get('orders'):
            one_level = level
            break
    if one_level: break
if one_level:
    print(f'    单个 level 结构: {json.dumps({k: (v if k != "orders" else v[:2]) for k, v in one_level.items()}, ensure_ascii=False, default=str)[:400]}')

# 多采几个时间点/变化点
for t in ['09:35:00.000', '11:00:00.000', '14:30:00.000']:
    s = viz.query_by_time(DATE, t)
    if s: sample_ids |= collect_ids(s)
for idx in [0, viz.get_total_changes() // 2, viz.get_total_changes() - 1]:
    s = viz.query_by_change_index(idx)
    if s: sample_ids |= collect_ids(s)
print(f'    多时点采样订单 ID 总数: {len(sample_ids)}')

# ---- 3. 与 csord CSV 的 orderid 对齐验证 ----
df = pd.read_csv(f'./data/csord_{SYM}_{DATE}.csv')
csv_ids = set(df['orderid'].astype('int64'))
print(f'\n[3] CSV 行数: {len(df)}, 唯一 orderid 数: {len(csv_ids)}')
inter = sample_ids & csv_ids
print(f'    快照采样 ID 数: {len(sample_ids)}, 命中 CSV: {len(inter)}, 命中率: {len(inter)/max(len(sample_ids),1)*100:.1f}%')
miss = sorted(sample_ids - csv_ids)[:10]
if miss:
    print(f'    未命中示例: {miss}')
# datetime 格式
print(f'    datetime 示例: {df["datetime"].iloc[0]} / {df["datetime"].iloc[-1]}')

# ---- 4. 引擎调用耗时 ----
import random
random.seed(42)
times = [f'{random.randint(9,14):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}.{random.randint(0,999):03d}' for _ in range(500)]
times = [t if t >= '09:30:00.000' else '09:30:00.000' for t in times]

t0 = time.time()
for t in times:
    viz.query_by_time(DATE, t)
d1 = (time.time()-t0)/len(times)*1000

t0 = time.time()
for t in times:
    viz.query_market_data(DATE, t)
d2 = (time.time()-t0)/len(times)*1000
print(f'\n[4] query_by_time 平均: {d1:.3f}ms/次 ({len(times)} 次采样)')
print(f'    query_market_data 平均: {d2:.3f}ms/次')
print(f'    => A2 后端循环 200 步预估: {d1*200:.0f}ms; C2 窗口内 60 采样点预估: {d2*60:.0f}ms')

# ---- 5. orderid→毫秒时间戳 映射构建开销 ----
t0 = time.time()
tracemalloc.start()
mapping = {}
dt_series = pd.to_datetime(df['datetime'])
base = pd.Timestamp(DATE)
ms_series = (dt_series - base).dt.total_seconds().mul(1000).astype('int64')
for oid, ms in zip(df['orderid'].astype('int64'), ms_series):
    mapping[int(oid)] = int(ms)
cur, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
build_ms = (time.time()-t0)*1000
print(f'\n[5] 映射构建: {len(mapping)} 条, 耗时 {build_ms:.0f}ms, 峰值内存 {peak/1024/1024:.1f}MB (含 pandas 读取)')
print(f'    查询示例: orderid {next(iter(mapping))} -> {mapping[next(iter(mapping))]} ms')

print('\n' + '=' * 60)
print('验证完成')
