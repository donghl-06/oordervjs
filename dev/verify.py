import pandas as pd
import numpy as np

trade_df = pd.read_csv('/home/linzhuoyu/project/wangcai_orderbook_cpp/cstra_000063.SZ_2024-12-19.csv')

cols = ["price", "size", "bidorderid", "askorderid"]
trade_df = trade_df[cols].reset_index(drop=True)
print(len(trade_df))
df = pd.read_csv('/home/linzhuoyu/project/wangcai_orderbook_cpp/backtest_trades_000063.SZ_2024-12-19.csv')
df['size'] = df['size'].astype(int)
df['bidorderid'] = df['bidorderid'].astype(int)
df['askorderid'] = df['askorderid'].astype(int)
df['price'] = df['price'].astype(float)
df = df[cols].reset_index(drop=True)
print(len(df))
# 只对齐长度最短的部分
n = min(len(trade_df), len(df))
trade_df = trade_df.iloc[:n]
df = df.iloc[:n]

# 对比各列
result = pd.DataFrame({
    'price_equal': np.isclose(trade_df['price'], df['price'], rtol=1e-9),
    'size_equal': trade_df['size'] == df['size'],
    'bid_equal': trade_df['bidorderid'] == df['bidorderid'],
    'ask_equal': trade_df['askorderid'] == df['askorderid'],
})

# 找出不相等的行
not_equal = ~result.all(axis=1)
diff_indices = np.where(not_equal)[0]

print(f"\n总共有 {len(diff_indices)} 行不相等")
for i in diff_indices[:5]:  # 只显示前5个不同的行
    print(f"\n第{i}行不相等:")
    print(f"trade_df: {trade_df.iloc[i].to_dict()}")
    print(f"df: {df.iloc[i].to_dict()}")