#!/usr/bin/env python3
"""order_local_id ↔ csord orderid 对齐校验（SZ/SH 通用）
用法：cd ordervis_server && ../.venv/bin/python test/check_alignment.py 000027.SZ 2025-08-01
"""
import sys
sys.path.insert(0, '/home/donghuale/project2-test')
sys.path.insert(0, '/home/donghuale/project2-test/ordervis_server')
sys.path.append('/home/donghuale/venv_adata/lib/python3.11/site-packages')

import pandas as pd
import lib.pywangcai_orderbook as wc

SYM = sys.argv[1] if len(sys.argv) > 1 else '000027.SZ'
DATE = sys.argv[2] if len(sys.argv) > 2 else '2025-08-01'

df = pd.read_csv(f'./data/csord_{SYM}_{DATE}.csv')
# 兼容两种格式：转换后(datetime 列) / 原始(date+time 列)
if 'datetime' not in df.columns:
    df['datetime'] = df['date'].astype(str) + ' ' + pd.to_timedelta(df['time']).astype(str)
csv_idx = df.set_index('orderid')

viz = wc.TradingVisualizer(SYM, DATE, './data/', False)
viz.run()

total = hit = consistent = 0
bad = []
n = viz.get_total_changes()
for idx in range(0, n, max(1, n // 6))[:6]:
    s = viz.query_by_change_index(idx)
    for name, level in s['levels'].items():
        side_sign = -1 if name.startswith('ask') else 1
        for o in level.get('orders', []):
            total += 1
            lid = int(o['order_local_id'])
            if lid not in csv_idx.index:
                if len(bad) < 5:
                    bad.append(f'local_id={lid} 不在CSV')
                continue
            hit += 1
            r = csv_idx.loc[lid]
            price_ok = abs(float(r['price']) * 10000 - level['price']) < 1 or float(r['price']) == 0
            side_ok = int(r['side']) == side_sign
            rem_ok = o['remaining_volume'] <= float(r['size'])
            if price_ok and side_ok and rem_ok:
                consistent += 1
            elif len(bad) < 5:
                bad.append(f'local_id={lid} price_csv={r["price"]} price_snap={level["price"]} side_csv={r["side"]}')

print(f'标的: {SYM} {DATE}')
print(f'采样订单: {total}, local_id 命中 CSV: {hit} ({hit/max(total,1)*100:.2f}%)')
print(f'价格/方向/量一致: {consistent} ({consistent/max(total,1)*100:.2f}%)')
for b in bad:
    print('  异常:', b)
print('结论:', '✅ 对齐可用' if hit / max(total, 1) >= 0.95 else '❌ 对齐失败，需换关联键')
