#!/usr/bin/env python3
"""第1步接口验证：create_time / next_change / trade_flow_series / order_lifecycle
运行：cd ordervis_server && ../.venv/bin/python verify_step1.py
"""
import sys, time
sys.path.insert(0, '/home/donghuale/project2-test')
sys.path.insert(0, '/home/donghuale/project2-test/ordervis_server')
sys.path.append('/home/donghuale/venv_adata/lib/python3.11/site-packages')

from ordervis_server.utils.tradebook import TradeBook

SYM, DATE = '000027.SZ', '2025-08-01'
print('=' * 60)
tb = TradeBook(SYM, DATE, './data/')

# 等待后台映射构建完成
t0 = time.time()
while tb._order_time_map is None and time.time() - t0 < 10:
    time.sleep(0.2)
print(f'[B2] create_time 映射: {len(tb._order_time_map or {})} 条, 等待 {time.time()-t0:.1f}s')

# 1. 快照 create_time 补全
snap = tb.get_snapshot_by_time('10:00:00.000')
orders = [(n, o) for n, l in snap['levels'].items() for o in l.get('orders', [])]
with_ct = sum(1 for _, o in orders if o.get('create_time'))
print(f'[B2] 10:00 快照订单 {len(orders)} 笔, 带 create_time: {with_ct}')
sample_order = orders[0][1]
print(f'     示例: local_id={sample_order["order_local_id"]} create_time={sample_order.get("create_time")}')

# 2. next_change 双向
t0 = time.time()
nxt = tb.get_adjacent_change('10:00:00.000', 1)
d1 = (time.time()-t0)*1000
t0 = time.time()
prv = tb.get_adjacent_change('10:00:00.000', -1)
d2 = (time.time()-t0)*1000
print(f'[A2] 下一变化: ts={nxt["timestamp"]} idx={nxt["change_index"]} ({d1:.0f}ms)')
print(f'[A2] 上一变化: ts={prv["timestamp"]} idx={prv["change_index"]} ({d2:.0f}ms)')
print(f'[A2] 边界(尾盘之后): {tb.get_adjacent_change("14:59:59.999", 1)}')

# 3. trade_flow_series
t0 = time.time()
series = tb.get_trade_flow_series('10:00:00.000', 3000, 60)
d3 = (time.time()-t0)*1000
nonzero = sum(1 for b in series if any(b[k] for k in ('bid_create','bid_cancel','bid_traded','ask_create','ask_cancel','ask_traded')))
print(f'[C2] 3s 窗口 {len(series)} 桶 ({d3:.0f}ms), 非空桶: {nonzero}')
print(f'     示例桶: {series[30]}')

# 4. order_lifecycle（用快照里真实存在的订单）
lid = int(sample_order['order_local_id'])
t0 = time.time()
lc = tb.get_order_lifecycle(lid)
d4 = (time.time()-t0)*1000
print(f'[B4] 订单 {lid} 生命周期 ({d4:.0f}ms): success={lc["success"]}')
if lc['success']:
    print(f'     summary: {lc["summary"]}')
    for e in lc['events'][:5]:
        print(f'     event: {e["time"]} {e["type"]} size={e["size"]} remaining={e["remaining_after"]} queue={e["queue"]}')
print('=' * 60)
