import os
import pandas as pd
import numpy as np
import aqdatac as aq
from datetime import time as datetime_time
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

class OptimizedRecoverEngine:
    def __init__(self, usr_name=None, usr_pwd=None):
        if usr_name is None:
            usr_name = os.environ.get("MY_USER_NAME")
        if usr_pwd is None:
            usr_pwd = os.environ.get("MY_PASSWORD")
        self.usr_name = usr_name
        self.usr_pwd = usr_pwd
        aq.login(usr_name, usr_pwd)
        self.order_df = pd.DataFrame()
        self.trade_df = pd.DataFrame()
        self.recover_df = pd.DataFrame()

        # 优化数据结构
        self.processed_orderids = set() 
        self.order_id_array = None  # 使用numpy数组
        self.bid_trades_dict = {}  # 使用普通字典
        self.ask_trades_dict = {}

    def __is_continuous__(self, t):
        """向量化的时间检查"""
        start_time = datetime_time(9, 30)
        if hasattr(t, '__iter__'):
            return np.array([start_time <= time_val for time_val in t])
        return start_time <= t

    def __get_data__(self, date, sym):
        print("正在获取数据...")
        if not os.path.exists(f"data/{date}"):
            os.makedirs(f"data/{date}")

        self.order_df = aq.get_data("csord", date, date, sym)
        self.trade_df = aq.get_data("cstra", date, date, sym)
        self.stick_df = aq.get_data("cstick", date, date, sym)

        print(f"原始数据大小: order={len(self.order_df)}, trade={len(self.trade_df)}")

        # 向量化数据预处理
        self.order_df['source'] = 'order'
        self.trade_df['source'] = 'trade'

        # 优化：避免reset_index
        if not self.order_df.index.is_monotonic_increasing:
            self.order_df.reset_index(drop=True, inplace=True)
        if not self.trade_df.index.is_monotonic_increasing:
            self.trade_df.reset_index(drop=True, inplace=True)

        # 向量化类型转换
        if 'exectype' in self.trade_df.columns:
            # 批量转换exectype
            exectype_values = self.trade_df["exectype"].values
            converted_exectype = np.array([
                x.decode().strip() if isinstance(x, bytes) else str(x) 
                for x in exectype_values
            ])
            self.trade_df["exectype"] = converted_exectype
            # 向量化过滤
            self.trade_df = self.trade_df[self.trade_df['exectype'] != '2']

        if 'tradebsflag' in self.trade_df.columns:
            # 批量转换tradebsflag
            bsflag_values = self.trade_df["tradebsflag"].values
            converted_bsflag = np.array([
                x.decode().strip() if isinstance(x, bytes) else str(x)
                for x in bsflag_values
            ])
            self.trade_df["tradebsflag"] = converted_bsflag

        # 并行保存CSV（如果需要）
        self.order_df.to_csv(f"data/csord_{sym}_{date}.csv", index=False)
        self.trade_df.to_csv(f"data/cstra_{sym}_{date}.csv", index=False)
        self.stick_df.to_csv(f"data/cstick_{sym}_{date}.csv", index=False)

        # 优化索引构建
        self._build_indices_optimized()

    def _build_indices_optimized(self):
        """优化的索引构建 - 使用numpy和向量化操作"""
        print("正在建立索引...")

        # 使用numpy数组加速
        self.order_id_array = self.order_df['orderid'].dropna().values

        # 向量化构建交易字典
        trade_array = self.trade_df[['bidorderid', 'askorderid']].values
        trade_indices = np.arange(len(self.trade_df))

        # 批量处理bid orders
        bid_mask = ~pd.isna(self.trade_df['bidorderid'].values) & (self.trade_df['bidorderid'].values != 0)
        bid_orderids = self.trade_df.loc[bid_mask, 'bidorderid'].values
        bid_indices = trade_indices[bid_mask]

        # 使用numpy的unique进行分组
        unique_bids, inverse_indices = np.unique(bid_orderids, return_inverse=True)
        for i, orderid in enumerate(unique_bids):
            self.bid_trades_dict[orderid] = bid_indices[inverse_indices == i].tolist()

        # 批量处理ask orders
        ask_mask = ~pd.isna(self.trade_df['askorderid'].values) & (self.trade_df['askorderid'].values != 0)
        ask_orderids = self.trade_df.loc[ask_mask, 'askorderid'].values
        ask_indices = trade_indices[ask_mask]

        unique_asks, inverse_indices = np.unique(ask_orderids, return_inverse=True)
        for i, orderid in enumerate(unique_asks):
            self.ask_trades_dict[orderid] = ask_indices[inverse_indices == i].tolist()

        print(f"索引建立完成: bid_trades={len(self.bid_trades_dict)}, ask_trades={len(self.ask_trades_dict)}")

    def _process_orders_batch_vectorized(self, orders_df):
        """完全向量化的批量处理"""
        print("正在向量化批量处理orders...")

        # 过滤已处理的订单
        mask = ~orders_df['orderid'].isin(self.processed_orderids) & orders_df['orderid'].notna()
        filtered_orders = orders_df[mask].copy()

        if filtered_orders.empty:
            return []

        # 预分配结果数组
        result_sizes = filtered_orders['size'].values.copy()
        orderids = filtered_orders['orderid'].values
        sides = filtered_orders['side'].values
        bizindexes = filtered_orders['bizindex'].values

        # 批量计算所有订单的交易总量
        for i, (orderid, side, bizindex) in enumerate(zip(orderids, sides, bizindexes)):
            # 获取相关交易索引
            if side == 1:
                trade_indices = self.bid_trades_dict.get(orderid, [])
            else:
                trade_indices = self.ask_trades_dict.get(orderid, [])

            if trade_indices:
                # 向量化过滤和求和
                trade_bizindexes = self.trade_df.iloc[trade_indices]['bizindex'].values
                valid_mask = trade_bizindexes <= bizindex
                if valid_mask.any():
                    valid_sizes = self.trade_df.iloc[trade_indices].loc[
                        self.trade_df.iloc[trade_indices]['bizindex'] <= bizindex, 'size'
                    ].values
                    result_sizes[i] += valid_sizes.sum()

        # 更新size列
        filtered_orders['size'] = result_sizes

        # 批量更新processed_orderids
        self.processed_orderids.update(orderids)

        return filtered_orders.to_dict('records')

    def _create_orders_from_missing_trades_vectorized(self):
        """向量化创建缺失的订单"""
        print("正在处理缺失的trade orders...")

        # 使用set操作找出缺失的订单
        order_id_set = set(self.order_id_array) | self.processed_orderids

        missing_bid_orderids = set(self.bid_trades_dict.keys()) - order_id_set
        missing_ask_orderids = set(self.ask_trades_dict.keys()) - order_id_set

        # 过滤无效ID
        missing_bid_orderids = {oid for oid in missing_bid_orderids if pd.notna(oid) and oid != 0}
        missing_ask_orderids = {oid for oid in missing_ask_orderids if pd.notna(oid) and oid != 0}

        print(f"发现缺失订单: bid={len(missing_bid_orderids)}, ask={len(missing_ask_orderids)}")

        new_orders = []

        # 批量处理买单
        if missing_bid_orderids:
            new_orders.extend(self._create_orders_batch(missing_bid_orderids, self.bid_trades_dict, 1))

        # 批量处理卖单
        if missing_ask_orderids:
            new_orders.extend(self._create_orders_batch(missing_ask_orderids, self.ask_trades_dict, -1))

        return new_orders

    def _create_orders_batch(self, orderids, trades_dict, side):
        """批量创建订单"""
        orders = []

        for orderid in orderids:
            trade_indices = trades_dict[orderid]
            if not trade_indices:
                continue

            # 批量获取交易数据
            trades = self.trade_df.iloc[trade_indices]
            if trades.empty:
                continue

            # 使用向量化操作计算聚合值
            first_trade = trades.iloc[trades['bizindex'].argmin()]

            new_order = {
                'orderid': orderid,
                'datetime': first_trade['datetime'],
                'bizindex': first_trade['bizindex'],
                'size': trades['size'].sum(),
                'side': side,
                'source': 'order',
                'ordertype': 0,
                'price': trades['price'].max() if side == 1 else trades['price'].min(),
                'channelno': first_trade.get('channelno', 0),
                'seqno': first_trade.get('seqno', 0)
            }

            # 复制其他必要字段
            for col in ['sym']:
                if col in first_trade:
                    new_order[col] = first_trade[col]

            orders.append(new_order)
            self.processed_orderids.add(orderid)

        return orders

    def __recover__(self, date, sym):
        """优化后的恢复算法"""
        print(f"开始恢复数据: {sym} {date}")
        self.__get_data__(date, sym)

        # 合并数据
        merge_df = pd.concat([self.trade_df, self.order_df], ignore_index=True)
        merge_df.sort_values(by=["bizindex"], inplace=True)
        merge_df.to_csv(f"data/{date}/{sym}_merge.csv", index=False)

        # 向量化时间过滤
        print("正在过滤时间段...")

        # 批量转换时间
        datetime_values = self.order_df['datetime'].values
        time_values = pd.to_datetime(datetime_values).to_series().dt.time
        continuous_mask = self.__is_continuous__(time_values)

        continuous_orders = self.order_df[continuous_mask].copy()
        non_continuous_orders = self.order_df[~continuous_mask].copy()

        print(f"连续时间段orders: {len(continuous_orders)}, 非连续: {len(non_continuous_orders)}")

        # 收集所有恢复的订单
        recovered_orders = []

        # 1. 处理连续时间段的orders（向量化）
        if not continuous_orders.empty:
            recovered_orders.extend(self._process_orders_batch_vectorized(continuous_orders))

        # 2. 处理非连续时间段的orders（向量化转换）
        if not non_continuous_orders.empty:
            recovered_orders.extend(non_continuous_orders.to_dict('records'))

        # 3. 处理缺失的trade orders（向量化）
        new_orders = self._create_orders_from_missing_trades_vectorized()
        recovered_orders.extend(new_orders)

        # 构建最终结果（向量化操作）
        if recovered_orders:
            print("正在构建最终DataFrame...")
            self.recover_df = pd.DataFrame(recovered_orders)

            # 向量化清理
            valid_mask = self.recover_df['orderid'].notna() & (self.recover_df['orderid'] != 0)
            self.recover_df = self.recover_df[valid_mask]

            # 类型转换
            self.recover_df['bizindex'] = self.recover_df['bizindex'].astype(np.int64)

            # 高效去重
            self.recover_df.drop_duplicates(subset=['orderid'], inplace=True)
            self.recover_df.sort_values(by=['bizindex'], inplace=True)
            self.recover_df.reset_index(drop=True, inplace=True)

            # 选择列
            col = ['datetime', 'sym', 'price', 'size', 'side', 'ordertype', 
                   'orderid', 'channelno', 'seqno', 'bizindex']
            existing_cols = [c for c in col if c in self.recover_df.columns]
            self.recover_df = self.recover_df[existing_cols]

            # 保存结果
            self.recover_df.to_csv(f"data/recovered_{sym}_{date}.csv", index=False)
            print(f"Successfully recovered {len(self.recover_df)} orders")
            print(f"Saved to: data/recovered_{sym}_{date}.csv")
        else:
            print("No orders recovered")

        return self.recover_df


# 可选：使用numba加速的辅助函数
try:
    from numba import jit, prange

    @jit(nopython=True, parallel=True)
    def fast_aggregate_trades(trade_sizes, trade_bizindexes, order_bizindexes):
        """使用numba加速的交易聚合"""
        n_orders = len(order_bizindexes)
        result = np.zeros(n_orders)

        for i in prange(n_orders):
            order_biz = order_bizindexes[i]
            mask = trade_bizindexes <= order_biz
            result[i] = np.sum(trade_sizes[mask])

        return result

    print("Numba加速已启用")
except ImportError:
    print("Numba未安装，使用纯Python实现")


if __name__ == "__main__":
    import time

    sym, date = "600050.SH", "2025-02-17"

    start_time = time.time()
    recover_engine = OptimizedRecoverEngine()
    result = recover_engine.__recover__(date, sym)
    end_time = time.time()

    print(f"\n总耗时: {end_time - start_time:.2f} 秒")
    print(f"恢复订单数量: {len(result)}")
    if not result.empty:
        print("\n前5行结果:")
        print(result.head())