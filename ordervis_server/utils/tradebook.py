
import lib.pywangcai_orderbook as wc
import time
import threading
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable, Union, List
from threading import Lock
import os

from ordervis_server.package import backend_logger

# 连续竞价开始时间（引擎 market_data 在该时间前无效）
CONTINUOUS_AUCTION_START_MS = 9 * 3600000 + 30 * 60000  # 09:30:00.000


def _time_to_ms(time_str: str) -> int:
    """'HH:MM:SS.mmm' -> 毫秒数"""
    if '.' not in time_str:
        time_str += '.000'
    h, m, rest = time_str.split(':')
    s, ms = rest.split('.')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def _ms_to_time(ms_value: int) -> str:
    """毫秒数 -> 'HH:MM:SS.mmm'"""
    h, ms_value = divmod(ms_value, 3600000)
    m, ms_value = divmod(ms_value, 60000)
    s, ms = divmod(ms_value, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


# 默认数据目录固定到服务端目录，不依赖启动时的当前工作目录。
DEFAULT_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
os.makedirs(DEFAULT_DATA_PATH, exist_ok=True)


class TradeBook:
    def __init__(self, symbol: str, date: str, data_path: str = DEFAULT_DATA_PATH, progress_callback: Optional[Callable] = None, is_ETF: bool = False):
        """初始化TradeBook"""
        self.symbol = symbol
        self.date = date
        self.data_path = data_path
        self.is_ETF = is_ETF
        self.visualizer = wc.TradingVisualizer(symbol, date, data_path, is_ETF)
        
        # 使用进度回调运行初始化
        if progress_callback:
            self.visualizer.run_with_progress(progress_callback)
        else:
            self.visualizer.run()
            
        self.last_accessed_at = datetime.now()
        self._lock = Lock()

        # 日志
        self.logger = backend_logger.Log("tradebook")
        self.log_level = backend_logger.LogLevel

        # orderid(=快照order_local_id) -> 下单时间 的轻量映射（后台懒构建）
        self._order_time_map: Optional[Dict[int, str]] = None
        self._map_building = False
        self._map_lock = Lock()

        # 逐笔数据缓存（懒加载）
        self._csord_df: Optional[pd.DataFrame] = None
        self._cstra_df: Optional[pd.DataFrame] = None
        self._order_price_map: Optional[Dict[int, float]] = None
        self._best_cancel_records: Optional[List[Dict]] = None
        self._trade_price_records: Optional[List[Dict]] = None
        self._order_meta_map: Optional[Dict[int, Dict[str, Any]]] = None
        self._passive_trade_records: Optional[List[Dict[str, Any]]] = None

        # 后台构建 create_time 映射，不阻塞初始化
        threading.Thread(target=self._build_order_time_map, daemon=True).start()

    # ---------- create_time 映射（B2） ----------

    def _csord_path(self) -> str:
        return os.path.join(self.data_path, f"csord_{self.symbol}_{self.date}.csv")

    def _cstra_path(self) -> str:
        return os.path.join(self.data_path, f"cstra_{self.symbol}_{self.date}.csv")

    def _build_order_time_map(self):
        """后台构建 orderid -> datetime 映射，并抽样自检对齐命中率"""
        with self._map_lock:
            if self._map_building or self._order_time_map is not None:
                return
            self._map_building = True
        try:
            path = self._csord_path()
            if not os.path.exists(path):
                self.logger.n_log(f"create_time 映射构建跳过，文件不存在: {path}", self.log_level.WARNING)
                return
            df = pd.read_csv(path, usecols=['orderid', 'datetime'])
            mapping = dict(zip(df['orderid'].astype('int64'), df['datetime'].astype(str)))
            self._order_time_map = mapping
            self.logger.n_log(f"create_time 映射构建完成: {self.get_key()}, {len(mapping)} 条", self.log_level.INFO)
            self._selfcheck_alignment()
        except Exception as e:
            self.logger.n_log(f"create_time 映射构建失败: {self.get_key()}, 错误: {e}", self.log_level.ERROR)
        finally:
            with self._map_lock:
                self._map_building = False

    def _selfcheck_alignment(self, sample_size: int = 100):
        """抽样验证快照订单 order_local_id 在映射中的命中率，低于95%打warning
        （上交所 csord 经 sh_revert_module 重建，订单号口径可能不同）"""
        try:
            total = self.visualizer.get_total_changes()
            if total <= 0:
                return
            snap = self.visualizer.query_by_change_index(total // 2)
            local_ids = [
                int(o['order_local_id'])
                for level in snap.get('levels', {}).values()
                for o in level.get('orders', [])
            ][:sample_size]
            if not local_ids:
                return
            hit = sum(1 for lid in local_ids if lid in self._order_time_map)
            rate = hit / len(local_ids)
            if rate < 0.95:
                self.logger.n_log(
                    f"[对齐自检] {self.get_key()} order_local_id 命中率仅 {rate*100:.1f}% "
                    f"({hit}/{len(local_ids)})，create_time 可能大面积缺失，请检查该标的的 orderid 口径",
                    self.log_level.WARNING,
                )
            else:
                self.logger.n_log(f"[对齐自检] {self.get_key()} 命中率 {rate*100:.1f}%", self.log_level.INFO)
        except Exception as e:
            self.logger.n_log(f"[对齐自检] {self.get_key()} 异常: {e}", self.log_level.ERROR)

    def _enrich_snapshot_create_time(self, snapshot: Optional[Dict]) -> Optional[Dict]:
        """为快照中的每笔订单补充 create_time（映射未就绪时保持原样）"""
        if snapshot is None or self._order_time_map is None:
            return snapshot
        mapping = self._order_time_map
        for level in snapshot.get('levels', {}).values():
            for order in level.get('orders', []):
                try:
                    order['create_time'] = mapping.get(int(order.get('order_local_id')))
                except (TypeError, ValueError):
                    order['create_time'] = None
        return snapshot

    # ---------- 相邻变化导航（A2） ----------

    def get_adjacent_change(self, time_str: str, direction: int = 1) -> Optional[Dict]:
        """
        获取指定时间之后(或之前)第一个有变化的快照。

        引擎坑位（实测 000027.SZ/2025-08-01）：
        - query_market_data 的 change_index 会滞后快照 1 位（14:59:59.999 处
          快照 ci=27396 而 md.ci=27395），不能作为基准；
        - query_by_time 返回的快照 timestamp 可靠（= 最后一个 ts<=T 的变化），
          但其 change_index 字段在部分时刻也会滞后 1 位（尾部返回 ci=27395
          而 query_by_change_index(27396) 才对应同一 ts）；
        - query_by_change_index 对越界 index 会钳制到端点快照。
        因此以「时间戳比较」为准：在 ci±1 两个候选中找第一个满足
        ts > ts_cur（direction=1）或 ts < ts_cur（direction=-1）的变化。

        Args:
            time_str: 'HH:MM:SS.mmm'
            direction: 1=下一个变化, -1=上一个变化
        Returns:
            完整快照 dict；没有更多变化时返回 None
        """
        self.update_access_time()
        current = self.get_snapshot_by_time(time_str)
        if not current:
            return None
        ts_cur = current.get('timestamp') or ''
        try:
            ci = int(current.get('change_index', -1))
        except (TypeError, ValueError):
            return None
        if ci < 0 or not ts_cur:
            return None

        total = self.visualizer.get_total_changes()
        forward = direction >= 0
        # 两个候选足以覆盖 change_index 滞后 1 位的情况
        candidates = [ci + 1, ci + 2] if forward else [ci, ci - 1]
        for k in candidates:
            if k < 0 or k >= total:
                continue
            s = self.visualizer.query_by_change_index(k)
            if not s:
                continue
            # 引擎越界钳制防护：返回的必须是目标变化本身
            if int(s.get('change_index', -1)) != k:
                continue
            ts = s.get('timestamp') or ''
            if not ts:
                continue
            if (forward and ts > ts_cur) or (not forward and ts < ts_cur):
                return self._enrich_snapshot_create_time(s)
        return None

    # ---------- 流量时间序列（C2） ----------

    def _best_level_cancel_volumes(self, start_ms: int, end_ms: int) -> List[Dict]:
        """
        修补引擎撤单计数器（恒为0）：从 cstra 撤单记录(et=2)计算买一/卖一撤单量。
        判定：撤单按 orderid 归属买/卖侧；该订单挂单价 == 撤单时刻买一/卖一价 → 计入一档。
        Returns: [{'time_ms': ..., 'side': 'bid'|'ask', 'volume': ...}, ...]
        """
        if self._best_cancel_records is not None:
            return [r for r in self._best_cancel_records if start_ms < r['time_ms'] <= end_ms]

        self._load_tick_data()
        records = []
        if self._cstra_df is None or self._csord_df is None:
            return records
        try:
            # 撤单行
            et = self._cstra_df['exectype'].astype(str).str.strip("b' ")
            cancels = self._cstra_df[et == '2']
            if cancels.empty:
                return records
            # orderid -> price 映射（懒构建缓存）
            if self._order_price_map is None:
                self._order_price_map = dict(zip(
                    self._csord_df['orderid'].astype('int64'), self._csord_df['price'].astype(float)
                ))
            start_str = f"{self.date} {_ms_to_time(CONTINUOUS_AUCTION_START_MS)}"
            end_str = f"{self.date} 15:00:00.000"
            win = cancels[(cancels['datetime'] > start_str) & (cancels['datetime'] <= end_str)]
            for _, row in win.iterrows():
                bid_oid = int(row['bidorderid'])
                ask_oid = int(row['askorderid'])
                oid = bid_oid if bid_oid != 0 else ask_oid
                side = 1 if bid_oid != 0 else -1
                price = self._order_price_map.get(oid)
                if price is None or price == 0:
                    continue  # 市价单等无法判档
                time_part = str(row['datetime']).split(' ')[-1]
                md = self.visualizer.query_market_data(self.date, time_part)
                if not md or not md.get('market_data'):
                    continue
                mdd = md['market_data']
                best_bid = (mdd.get('best_bids') or [None])[0]
                best_ask = (mdd.get('best_asks') or [None])[0]
                price_int = round(price * 10000)
                if side == 1 and best_bid is not None and price_int == best_bid:
                    records.append({'time_ms': _time_to_ms(time_part), 'side': 'bid', 'volume': float(row['size'])})
                elif side == -1 and best_ask is not None and price_int == best_ask:
                    records.append({'time_ms': _time_to_ms(time_part), 'side': 'ask', 'volume': float(row['size'])})
        except Exception as e:
            self.logger.n_log(f"撤单量修补计算失败: {self.get_key()}, 错误: {e}", self.log_level.ERROR)
        self._best_cancel_records = sorted(records, key=lambda r: r['time_ms'])
        return [r for r in self._best_cancel_records if start_ms < r['time_ms'] <= end_ms]

    def _get_trade_price_records(self, start_ms: int, end_ms: int) -> List[Dict]:
        """返回时间范围内的逐笔成交价，结果按时间排序并缓存。"""
        if self._trade_price_records is None:
            self._load_tick_data()
            records = []
            if self._cstra_df is not None:
                try:
                    et = self._cstra_df["exectype"].astype(str).map(self._clean_exectype)
                    trades = self._cstra_df[et == "1"]
                    for _, row in trades.iterrows():
                        time_part = str(row["datetime"]).split(" ")[-1]
                        price = float(row["price"])
                        if price > 0:
                            records.append({"time_ms": _time_to_ms(time_part), "price": price})
                except Exception as e:
                    self.logger.n_log(f"成交价缓存构建失败: {self.get_key()}, 错误: {e}", self.log_level.ERROR)
            self._trade_price_records = sorted(records, key=lambda r: r["time_ms"])
        return [r for r in self._trade_price_records if start_ms < r["time_ms"] <= end_ms]

    def get_trade_flow_series(self, time_str: str, window_ms: int, points: int = 60) -> List[Dict]:
        """
        获取 [time-window, time] 窗口内买一/卖一的流量序列 + 一档盘口等待量。
        在窗口内均匀取 points+1 个采样点查 market_data（0.013ms/次），
        相邻采样点的累计量差分即每桶新增量。

        Returns: [{'start': 'HH:MM:SS.mmm', 'end': ..., 'bid_create': ..., 'bid_cancel': ...,
                   'bid_traded': ..., 'ask_create': ..., 'ask_cancel': ..., 'ask_traded': ...,
                   'bid_volume': ..., 'ask_volume': ...}, ...]
        注：
        - create/traded 用引擎计数器差分；cancel 引擎计数器恒0，用 CSV 修补（见 _best_level_cancel_volumes）。
        - bid_volume/ask_volume = 该桶右缘时刻真实买一/卖一盘口累计等待量（状态量，非差分）。
          最优价会在窗口内变化，不能用右缘档位和累计计数器反推历史一档量；因此逐采样点
          查询完整快照，保证每个图上时刻都取该时刻实际买一/卖一的 total_volume。
        """
        self.update_access_time()
        end_ms = _time_to_ms(time_str)
        start_ms = max(end_ms - int(window_ms), CONTINUOUS_AUCTION_START_MS)
        points = max(2, min(int(points), 500))
        step = (end_ms - start_ms) / points
        if step <= 0:
            return []

        sample_times = [_ms_to_time(round(start_ms + i * step)) for i in range(points + 1)]
        snapshots = [self.visualizer.query_market_data(self.date, t) for t in sample_times]

        # 撤单修补：同一份日内记录同时生成桶内瞬时量和截至桶右缘的累计量。
        all_cancel_records = self._best_level_cancel_volumes(CONTINUOUS_AUCTION_START_MS - 1, end_ms)
        bucket_cancel = [{'bid': 0.0, 'ask': 0.0} for _ in range(points)]
        for rec in all_cancel_records:
            if rec['time_ms'] <= start_ms:
                continue
            idx = int((rec['time_ms'] - start_ms) / step)
            idx = min(max(idx, 0), points - 1)
            bucket_cancel[idx][rec['side']] += rec['volume']

        cumulative_cancel = []
        running_cancel = {'bid': 0.0, 'ask': 0.0}
        cancel_index = 0
        for sample_time in sample_times[1:]:
            sample_ms = _time_to_ms(sample_time)
            while cancel_index < len(all_cancel_records) and all_cancel_records[cancel_index]['time_ms'] <= sample_ms:
                rec = all_cancel_records[cancel_index]
                running_cancel[rec['side']] += rec['volume']
                cancel_index += 1
            cumulative_cancel.append(dict(running_cancel))

        # 一档状态量必须按采样时刻读取真实快照。累计计数器只描述流量，最优价切档后
        # 无法从窗口右缘的一档反推出历史时刻的“一档”，此前的反推会产生伪 0。
        level_snapshots = [self.visualizer.query_by_time(self.date, t) or {} for t in sample_times[1:]]

        def _level_price(bucket_index, side):
            levels = level_snapshots[bucket_index].get("levels") or {}
            level = levels.get(f"{side}1") or {}
            price = level.get("price")
            return float(price) / 10000 if price is not None else None

        trade_prices = [[] for _ in range(points)]
        for rec in self._get_trade_price_records(start_ms, end_ms):
            idx = int((rec["time_ms"] - start_ms) / step)
            idx = min(max(idx, 0), points - 1)
            if rec["price"] not in trade_prices[idx]:
                trade_prices[idx].append(rec["price"])

        def _level_volume(bucket_index, side):
            levels = level_snapshots[bucket_index].get('levels') or {}
            level = levels.get(f'{side}1') or {}
            volume = level.get('total_volume')
            return float(volume) if volume is not None else None

        series = []
        for i in range(points):
            cur = snapshots[i + 1].get('market_data') or {}
            prev = snapshots[i].get('market_data') or {}
            series.append({
                'start': sample_times[i],
                'end': sample_times[i + 1],
                'bid_create': (cur.get('bid_create_count') or 0) - (prev.get('bid_create_count') or 0),
                'bid_cancel': bucket_cancel[i]['bid'],
                'bid_cancel_cumulative': cumulative_cancel[i]['bid'],
                'bid_traded': (cur.get('bid_traded_count') or 0) - (prev.get('bid_traded_count') or 0),
                'bid_traded_cumulative': cur.get('bid_traded_count') or 0,
                'ask_create': (cur.get('ask_create_count') or 0) - (prev.get('ask_create_count') or 0),
                'ask_cancel': bucket_cancel[i]['ask'],
                'ask_cancel_cumulative': cumulative_cancel[i]['ask'],
                'ask_traded': (cur.get('ask_traded_count') or 0) - (prev.get('ask_traded_count') or 0),
                'ask_traded_cumulative': cur.get('ask_traded_count') or 0,
                # 桶右缘时刻的一档累计挂单量（盘口等待量）
                'bid_volume': _level_volume(i, 'bid'),
                'ask_volume': _level_volume(i, 'ask'),
                # 价格字段供 Q-t 图悬停提示使用：挂单看当时一档价，成交看桶内成交价。
                'bid_price': _level_price(i, 'bid'),
                'ask_price': _level_price(i, 'ask'),
                'trade_prices': trade_prices[i],
            })
        return series

    @classmethod
    def create_with_progress(cls, symbol: str, date: str, data_path: str = DEFAULT_DATA_PATH, progress_callback: Optional[Callable] = None, is_ETF: bool = False):
        """
        创建TradeBook实例的工厂方法，支持进度回调
        """
        return cls(symbol, date, data_path, progress_callback, is_ETF=is_ETF)

    def get_key(self) -> str:
        """获取唯一标识key"""
        return f"{self.symbol}_{self.date}"

    def update_access_time(self):
        """更新最后访问时间"""
        with self._lock:
            self.last_accessed_at = datetime.now()

    def is_expired(self, hours: float = 12.0) -> bool:
        """检查是否过期 """
        expiry_time = self.last_accessed_at + timedelta(hours=hours)
        return datetime.now() > expiry_time

    def get_total_snapshots(self):
        """获取总快照数"""
        self.update_access_time()
        return self.visualizer.get_total_snapshots()
    
    def get_total_changes(self):
        """获取总变化数"""
        self.update_access_time()
        return self.visualizer.get_total_changes()
    
    def get_time_range(self):
        """获取时间范围"""
        self.update_access_time()
        return self.visualizer.get_time_range()
    
    def get_snapshot_by_time(self, time: str):
        """按照时间查询快照"""
        self.update_access_time()
        return self._enrich_snapshot_create_time(self.visualizer.query_by_time(self.date, time))

    def get_snapshot_by_id(self, id: int):
        """按照id查询快照"""
        self.update_access_time()
        return self._enrich_snapshot_create_time(self.visualizer.query_by_id(id))

    def get_snapshot_by_index(self, index: int):
        """按照索引查询快照"""
        self.update_access_time()
        return self._enrich_snapshot_create_time(self.visualizer.query_by_change_index(index))

    def get_market_data(self, time: str):
        """获取市场数据"""
        self.update_access_time()
        return self.visualizer.query_market_data(self.date, time)

    def get_idle_time(self) -> timedelta:
        """获取空闲时间"""
        return datetime.now() - self.last_accessed_at
    
    def get_orders_data(self):
        """读取与盘口回放一致的本地 csord 文件。"""
        local_path = self._csord_path()
        try:
            if not os.path.exists(local_path):
                self.logger.n_log(
                    f"本地订单数据不存在: {local_path}", self.log_level.ERROR
                )
                return None
            orders_df = pd.read_csv(local_path)

            if orders_df is None or len(orders_df) == 0:
                return None

            if 'datetime' not in orders_df.columns:
                if 'date' in orders_df.columns and 'time' in orders_df.columns:
                    orders_df['datetime'] = orders_df['date'] + pd.to_timedelta(orders_df['time'])
                else:
                    return None

            orders_df['datetime'] = pd.to_datetime(orders_df['datetime'], errors='coerce')
            for column in ('price', 'size', 'side', 'orderid'):
                if column in orders_df.columns:
                    orders_df[column] = pd.to_numeric(orders_df[column], errors='coerce')
            return orders_df.dropna(subset=['datetime', 'price', 'size', 'side', 'orderid'])
        except Exception as e:
            self.logger.n_log(f"读取订单数据失败: {self.get_key()}, 错误: {e}", self.log_level.ERROR)
            return None

    def find_order(self, order_time: Union[str, datetime], order_price: float, 
                   order_size: float, order_side: int, tolerance_ms: int = 100) -> Dict[str, Any]:
        """
        根据订单时间、价格、数量和方向查找订单
        
        Args:
            order_time: 订单时间 (字符串或datetime)
            order_price: 订单价格
            order_size: 订单数量
            order_side: 订单方向（1为买，-1为卖）
            tolerance_ms: 时间容差，单位为毫秒，默认100ms
            
        Returns:
            Dict包含查询结果
        """
        self.update_access_time()
        
        try:
            # 获取订单数据
            orders_df = self.get_orders_data()
            if orders_df is None or len(orders_df) == 0:
                return {
                    "success": False,
                    "orderid": None,
                    "datetime": None,
                    "message": "无法获取订单数据或数据为空"
                }

            # 转换时间；前端通常只传 HH:mm:ss.SSS，补上当前 TradeBook 日期。
            if isinstance(order_time, str):
                time_value = order_time.strip()
                target_time = pd.Timestamp(
                    f"{self.date} {time_value}" if ' ' not in time_value else time_value
                )
            else:
                target_time = pd.Timestamp(order_time)

            order_price = float(order_price)
            order_size = float(order_size)
            order_side = int(order_side)

            # 矢量化计算：价格、数量和方向的匹配
            price_match = (orders_df['price'] - order_price).abs() < 1e-6
            size_match = (orders_df['size'] - order_size).abs() < 1e-6
            side_match = orders_df['side'] == order_side
            combined_match = price_match & size_match & side_match

            # 第一步：查找时间大于等于给定时间的匹配订单
            time_forward_match = orders_df['datetime'] >= target_time
            forward_matches = orders_df[combined_match & time_forward_match]

            if len(forward_matches) > 0:
                # 选择时间最早的订单
                min_time = forward_matches['datetime'].min()
                first_match = forward_matches[forward_matches['datetime'] == min_time].iloc[0]
                return {
                    "success": True,
                    "orderid": int(first_match['orderid']),
                    "datetime": str(first_match['datetime']),
                    "price": float(first_match['price']),
                    "size": float(first_match['size']),
                    "side": int(first_match['side']),
                    "message": f"成功找到匹配的订单: ID={first_match['orderid']}"
                }

            # 第二步：向前查找容差时间内最接近下单时间的订单
            time_diff = target_time - orders_df['datetime']
            time_backward_match = (orders_df['datetime'] < target_time) & (time_diff < pd.Timedelta(f"{tolerance_ms}ms"))
            backward_matches = orders_df[combined_match & time_backward_match]

            if len(backward_matches) > 0:
                # 选择时间最接近的订单
                max_time = backward_matches['datetime'].max()
                first_match = backward_matches[backward_matches['datetime'] == max_time].iloc[0]
                return {
                    "success": True,
                    "orderid": int(first_match['orderid']),
                    "datetime": str(first_match['datetime']),
                    "price": float(first_match['price']),
                    "size": float(first_match['size']),
                    "side": int(first_match['side']),
                    "message": f"在容差时间内找到匹配的订单: ID={first_match['orderid']}"
                }

            # 未找到匹配订单
            return {
                "success": False,
                "orderid": None,
                "datetime": None,
                "message": "没有找到匹配的订单"
            }

        except Exception as e:
            return {
                "success": False,
                "orderid": None,
                "datetime": None,
                "message": f"查找订单时发生错误: {e}",
            }

    # ---------- 订单生命周期（B4） ----------

    @staticmethod
    def _clean_exectype(value) -> str:
        """cstra 的 exectype 形如 \"b'1'\"，剥离字节串包装"""
        s = str(value)
        if s.startswith("b'") and s.endswith("'"):
            s = s[2:-1]
        return s.strip()

    def _load_tick_data(self):
        """懒加载本标的的 csord/cstra CSV"""
        if self._csord_df is None and os.path.exists(self._csord_path()):
            self._csord_df = pd.read_csv(self._csord_path())
        if self._cstra_df is None and os.path.exists(self._cstra_path()):
            self._cstra_df = pd.read_csv(self._cstra_path())

    def _queue_positions_at(self, time_str: str, order_ids: List[int]) -> Dict[int, Dict]:
        """在指定时刻的一次快照中批量定位订单，返回队列位置与身前/身后量"""
        try:
            snap = self.visualizer.query_by_time(self.date, time_str)
            if not snap:
                return {}
            wanted = {int(order_id) for order_id in order_ids}
            positions = {}
            for level_key, level in snap.get('levels', {}).items():
                orders = level.get('orders', [])
                for i, o in enumerate(orders):
                    try:
                        current_id = int(o.get('order_local_id', -1))
                    except (TypeError, ValueError):
                        continue
                    if current_id in wanted:
                        ahead = sum(int(x.get('remaining_volume', 0)) for x in orders[:i])
                        behind = sum(int(x.get('remaining_volume', 0)) for x in orders[i + 1:])
                        positions[current_id] = {
                            'level': level_key,
                            'price': level.get('price'),
                            'position': i + 1,
                            'level_order_count': len(orders),
                            'remaining_volume': float(o.get('remaining_volume', 0) or 0),
                            'ahead_volume': ahead,
                            'behind_volume': behind,
                        }
            return positions
        except Exception:
            return {}

    def _queue_position_at(self, time_str: str, order_id: int) -> Optional[Dict]:
        """在指定时刻的快照中定位订单，返回队列位置与身前/身后量"""
        return self._queue_positions_at(time_str, [order_id]).get(order_id)

    def get_order_queue_series(
        self,
        time_str: str,
        window_ms: int,
        order_ids: List[int],
        points: int = 60,
    ) -> List[Dict]:
        """获取窗口内多个订单的队列位置、身前量和身后量序列。"""
        self.update_access_time()
        unique_ids = list(dict.fromkeys(int(order_id) for order_id in order_ids))
        if not unique_ids:
            return []

        end_ms = _time_to_ms(time_str)
        start_ms = max(end_ms - int(window_ms), CONTINUOUS_AUCTION_START_MS)
        points = max(2, min(int(points), 500))
        step = (end_ms - start_ms) / points
        if step <= 0:
            return []

        sample_times = [_ms_to_time(round(start_ms + i * step)) for i in range(points + 1)]
        series = []
        for sample_time in sample_times[1:]:
            positions = self._queue_positions_at(sample_time, unique_ids)
            series.append({
                'time': sample_time,
                'orders': {
                    str(order_id): positions.get(order_id)
                    for order_id in unique_ids
                },
            })
        return series

    def _ensure_execution_prediction_cache(self):
        """构建订单元数据和被动挂单成交记录，供成交时间预测复用。"""
        self._load_tick_data()
        if self._order_meta_map is None:
            order_meta: Dict[int, Dict[str, Any]] = {}
            if self._csord_df is not None:
                for _, row in self._csord_df.iterrows():
                    try:
                        order_id = int(row['orderid'])
                        timestamp = pd.Timestamp(row['datetime'])
                        time_ms = (
                            timestamp.hour * 3600000
                            + timestamp.minute * 60000
                            + timestamp.second * 1000
                            + timestamp.microsecond // 1000
                        )
                        order_meta[order_id] = {
                            'time_ms': time_ms,
                            'side': int(row['side']),
                            'price': float(row['price']),
                        }
                    except (TypeError, ValueError, KeyError):
                        continue
            self._order_meta_map = order_meta

        if self._passive_trade_records is not None:
            return

        records: List[Dict[str, Any]] = []
        if self._cstra_df is not None:
            exectypes = self._cstra_df['exectype'].astype(str).map(self._clean_exectype)
            trades = self._cstra_df[exectypes == '1']
            order_meta = self._order_meta_map or {}
            for _, row in trades.iterrows():
                try:
                    timestamp = pd.Timestamp(row['datetime'])
                    time_ms = (
                        timestamp.hour * 3600000
                        + timestamp.minute * 60000
                        + timestamp.second * 1000
                        + timestamp.microsecond // 1000
                    )
                    bid_id = int(row['bidorderid'])
                    ask_id = int(row['askorderid'])
                    flag = self._clean_exectype(row.get('tradebsflag', '0')).upper()

                    # B/S 表示主动买/主动卖；部分市场（如上交所）恒为 0，
                    # 此时用双方订单创建先后判断较早进入盘口的被动侧。
                    passive_side = None
                    if flag == 'B':
                        passive_side = -1
                    elif flag == 'S':
                        passive_side = 1
                    else:
                        bid_meta = order_meta.get(bid_id)
                        ask_meta = order_meta.get(ask_id)
                        if bid_meta and ask_meta:
                            if bid_meta['time_ms'] < ask_meta['time_ms']:
                                passive_side = 1
                            elif ask_meta['time_ms'] < bid_meta['time_ms']:
                                passive_side = -1

                    if passive_side is None:
                        continue
                    volume = float(row['size'])
                    price = float(row['price'])
                    if volume <= 0 or price <= 0:
                        continue
                    records.append({
                        'time_ms': time_ms,
                        'side': passive_side,
                        'price': price,
                        'volume': volume,
                    })
                except (TypeError, ValueError, KeyError):
                    continue
        self._passive_trade_records = sorted(records, key=lambda item: item['time_ms'])

    @staticmethod
    def _session_start_for_time(time_ms: int) -> int:
        afternoon_start = 13 * 3600000
        return afternoon_start if time_ms >= afternoon_start else CONTINUOUS_AUCTION_START_MS

    def _queue_depletion_sample(
        self,
        order_id: int,
        end_ms: int,
        window_ms: int,
        create_ms: int,
    ) -> Dict[str, Any]:
        """估计订单身前队列消耗速度；身前撤单和成交都会计入有效消耗。"""
        start_ms = max(
            end_ms - window_ms,
            self._session_start_for_time(end_ms),
            create_ms,
        )
        duration_ms = max(0, end_ms - start_ms)
        if duration_ms <= 0:
            return {
                'window_ms': window_ms,
                'actual_window_ms': 0,
                'rate': 0.0,
                'depleted_volume': 0.0,
                'observed_seconds': 0.0,
                'valid_samples': 0,
            }

        points = max(6, min(60, int(duration_ms / 500)))
        step = duration_ms / points
        weighted_depletion = 0.0
        weighted_seconds = 0.0
        raw_depletion = 0.0
        observed_seconds = 0.0
        valid_samples = 0
        previous = None
        half_life_seconds = max(5.0, duration_ms / 3000)

        for index in range(points + 1):
            sample_ms = round(start_ms + index * step)
            position = self._queue_position_at(_ms_to_time(sample_ms), order_id)
            if position is None:
                previous = None
                continue

            valid_samples += 1
            current_ahead = float(position.get('ahead_volume', 0) or 0)
            if previous is not None:
                previous_ms, previous_ahead = previous
                elapsed_seconds = max(0.0, (sample_ms - previous_ms) / 1000)
                if elapsed_seconds > 0:
                    depletion = max(0.0, previous_ahead - current_ahead)
                    age_seconds = max(0.0, (end_ms - sample_ms) / 1000)
                    weight = 0.5 ** (age_seconds / half_life_seconds)
                    weighted_depletion += depletion * weight
                    weighted_seconds += elapsed_seconds * weight
                    raw_depletion += depletion
                    observed_seconds += elapsed_seconds
            previous = (sample_ms, current_ahead)

        return {
            'window_ms': window_ms,
            'actual_window_ms': duration_ms,
            'rate': weighted_depletion / weighted_seconds if weighted_seconds > 0 else 0.0,
            'depleted_volume': raw_depletion,
            'observed_seconds': observed_seconds,
            'valid_samples': valid_samples,
        }

    def _same_price_trade_sample(
        self,
        side: int,
        price: float,
        end_ms: int,
        window_ms: int,
    ) -> Dict[str, Any]:
        """统计当前会话内同价格、同被动挂单方向的成交服务速度。"""
        start_ms = max(end_ms - window_ms, self._session_start_for_time(end_ms))
        elapsed_seconds = max(0.0, (end_ms - start_ms) / 1000)
        matching = [
            record for record in (self._passive_trade_records or [])
            if start_ms < record['time_ms'] <= end_ms
            and record['side'] == side
            and abs(record['price'] - price) < 0.000001
        ]
        volume = sum(record['volume'] for record in matching)
        return {
            'window_ms': window_ms,
            'actual_window_ms': end_ms - start_ms,
            'rate': volume / elapsed_seconds if elapsed_seconds > 0 else 0.0,
            'trade_volume': volume,
            'trade_count': len(matching),
            'average_trade_size': volume / len(matching) if matching else 0.0,
        }

    @staticmethod
    def _select_adaptive_sample(samples: List[Dict[str, Any]], sample_type: str) -> Dict[str, Any]:
        if sample_type == 'trade':
            for sample in samples:
                if sample['trade_count'] >= 3:
                    return sample
            for sample in reversed(samples):
                if sample['trade_count'] > 0:
                    return sample
        else:
            for sample in samples:
                if sample['rate'] > 0 and sample['observed_seconds'] >= 5:
                    return sample
            for sample in reversed(samples):
                if sample['valid_samples'] >= 2:
                    return sample
        return samples[-1]

    @staticmethod
    def _add_trading_wait(time_str: str, wait_seconds: Optional[float]) -> Dict[str, Any]:
        """在当日连续竞价时段内增加等待时间，自动跳过午休。"""
        if wait_seconds is None:
            return {'time': None, 'beyond_close': False}
        current_ms = _time_to_ms(time_str)
        remaining_ms = max(0, round(wait_seconds * 1000))
        morning_start = 9 * 3600000 + 30 * 60000
        morning_end = 11 * 3600000 + 30 * 60000
        afternoon_start = 13 * 3600000
        close_ms = 15 * 3600000

        if current_ms < morning_start:
            current_ms = morning_start
        if morning_end <= current_ms < afternoon_start:
            current_ms = afternoon_start

        while remaining_ms > 0:
            session_end = morning_end if current_ms < morning_end else close_ms
            available = max(0, session_end - current_ms)
            if remaining_ms <= available:
                return {'time': _ms_to_time(current_ms + remaining_ms), 'beyond_close': False}
            remaining_ms -= available
            if session_end == morning_end:
                current_ms = afternoon_start
            else:
                return {'time': None, 'beyond_close': True}
        return {'time': _ms_to_time(current_ms), 'beyond_close': False}

    def get_order_execution_estimate(self, time_str: str, order_id: int) -> Dict[str, Any]:
        """返回订单真实成交结果和仅使用 time_str 之前数据计算的成交时间预测。"""
        self.update_access_time()
        lifecycle = self.get_order_lifecycle(order_id)
        if not lifecycle.get('success'):
            return lifecycle

        self._ensure_execution_prediction_cache()
        summary = lifecycle['summary']
        events = lifecycle['events']
        trade_events = [event for event in events if event['type'] == 'trade']
        cancel_events = [event for event in events if event['type'] == 'cancel']
        full_fill_event = next(
            (event for event in trade_events if event.get('remaining_after', 1) <= 0),
            None,
        )
        actual = {
            'outcome': summary.get('outcome'),
            'first_fill_time': trade_events[0]['time'] if trade_events else None,
            'last_fill_time': trade_events[-1]['time'] if trade_events else None,
            'full_fill_time': full_fill_event['time'] if full_fill_event else None,
            'cancel_time': cancel_events[-1]['time'] if cancel_events else None,
            'filled_volume': summary.get('filled_size', 0),
            'cancelled_volume': summary.get('cancelled_size', 0),
            'trade_count': len(trade_events),
        }

        end_ms = _time_to_ms(time_str)
        past_trade_events = [
            event for event in trade_events
            if _time_to_ms(event['time'].split(' ')[-1]) <= end_ms
        ]
        has_filled_as_of = bool(past_trade_events)
        filled_volume_as_of = sum(float(event.get('size', 0) or 0) for event in past_trade_events)
        current_position = self._queue_position_at(time_str, order_id)
        meta = (self._order_meta_map or {}).get(order_id)
        if current_position is None or meta is None:
            return {
                'success': True,
                'order': summary,
                'as_of_time': time_str,
                'actual': actual,
                'prediction': {
                    'available': False,
                    'reason': '订单在当前快照六档盘口中不可见，无法取得当前身前量',
                    'lookahead_safe': True,
                },
            }

        candidate_windows = [30000, 120000, 600000]
        queue_samples = [
            self._queue_depletion_sample(order_id, end_ms, window, meta['time_ms'])
            for window in candidate_windows
        ]
        trade_samples = [
            self._same_price_trade_sample(meta['side'], meta['price'], end_ms, window)
            for window in candidate_windows
        ]
        queue_sample = self._select_adaptive_sample(queue_samples, 'queue')
        trade_sample = self._select_adaptive_sample(trade_samples, 'trade')

        ahead_volume = float(current_position.get('ahead_volume', 0) or 0)
        remaining_volume = float(current_position.get('remaining_volume', 0) or 0)
        queue_rate = float(queue_sample.get('rate', 0) or 0)
        trade_rate = float(trade_sample.get('rate', 0) or 0)
        effective_queue_rate = queue_rate if queue_rate > 0 else trade_rate
        warnings = []

        if trade_rate <= 0:
            first_wait = None
            full_wait = None
            warnings.append('统计窗口内没有可识别的同价位成交，暂时无法给出成交时间')
        else:
            queue_wait = ahead_volume / effective_queue_rate if effective_queue_rate > 0 else None
            if queue_wait is None:
                first_wait = None
                full_wait = None
            else:
                average_trade_size = float(trade_sample.get('average_trade_size', 0) or 0)
                typical_fill = min(remaining_volume, average_trade_size or remaining_volume)
                first_wait = queue_wait + typical_fill / trade_rate
                full_wait = queue_wait + remaining_volume / trade_rate

        level_key = str(current_position.get('level') or '')
        price_active = level_key in ('bid1', 'ask1')
        if not price_active:
            warnings.append('订单当前不在最优价，预测已包含近期无成交时段，但未单独预测价格何时到达该档位')
        if queue_rate <= 0:
            warnings.append('近期未观察到身前量下降，身前等待部分使用同价位成交速度估算')

        trade_count = int(trade_sample.get('trade_count', 0) or 0)
        observed_seconds = float(queue_sample.get('observed_seconds', 0) or 0)
        if trade_count >= 10 and observed_seconds >= 15:
            confidence = 'high'
        elif trade_count >= 3 or (trade_count > 0 and queue_rate > 0):
            confidence = 'medium'
        else:
            confidence = 'low'
        if not price_active and confidence == 'high':
            confidence = 'medium'

        first_clock = self._add_trading_wait(time_str, first_wait)
        full_clock = self._add_trading_wait(time_str, full_wait)
        return {
            'success': True,
            'order': summary,
            'as_of_time': time_str,
            'actual': actual,
            'current_queue': current_position,
            'prediction': {
                'available': first_wait is not None,
                'lookahead_safe': True,
                'confidence': confidence,
                'price_active': price_active,
                'has_filled_as_of': has_filled_as_of,
                'filled_volume_as_of': filled_volume_as_of,
                'first_fill_wait_ms': round(first_wait * 1000) if first_wait is not None else None,
                'full_fill_wait_ms': round(full_wait * 1000) if full_wait is not None else None,
                'first_fill_time': first_clock['time'],
                'full_fill_time': full_clock['time'],
                'first_fill_beyond_close': first_clock['beyond_close'],
                'full_fill_beyond_close': full_clock['beyond_close'],
                'queue_depletion_rate': queue_rate,
                'same_price_trade_rate': trade_rate,
                'warnings': warnings,
                'basis': {
                    'queue_window_ms': queue_sample['actual_window_ms'],
                    'queue_observed_seconds': observed_seconds,
                    'queue_depleted_volume': queue_sample.get('depleted_volume', 0),
                    'trade_window_ms': trade_sample['actual_window_ms'],
                    'trade_count': trade_count,
                    'trade_volume': trade_sample.get('trade_volume', 0),
                    'average_trade_size': trade_sample.get('average_trade_size', 0),
                },
            },
        }
    def get_order_lifecycle(self, order_id: int) -> Dict[str, Any]:
        """
        重建订单生命周期：挂出 -> 逐笔成交/撤单 -> 终结。
        order_id 为 CSV 的 orderid（即快照中的 order_local_id）。
        """
        self.update_access_time()
        self._load_tick_data()

        if self._csord_df is None:
            return {"success": False, "message": "csord 数据文件不存在"}

        # 出生事件：csord 中按 orderid 定位
        born = self._csord_df[self._csord_df['orderid'].astype('int64') == order_id]
        if born.empty:
            return {"success": False, "message": f"订单 {order_id} 在 csord 中不存在"}
        born_row = born.sort_values('datetime').iloc[0]

        events: List[Dict] = [{
            'time': str(born_row['datetime']),
            'type': 'create',
            'size': float(born_row['size']),
            'price': float(born_row['price']),
            'remaining_after': float(born_row['size']),
        }]
        remaining = float(born_row['size'])

        # 后续事件：cstra 中按 bid/ask orderid 关联，exectype '1'=成交 '2'=撤单
        if self._cstra_df is not None:
            tra = self._cstra_df[
                (self._cstra_df['bidorderid'].astype('int64') == order_id) |
                (self._cstra_df['askorderid'].astype('int64') == order_id)
            ].sort_values('datetime')
            for _, row in tra.iterrows():
                exectype = self._clean_exectype(row['exectype'])
                event_type = 'trade' if exectype == '1' else ('cancel' if exectype == '2' else f'unknown({exectype})')
                remaining = max(0.0, remaining - float(row['size']))
                events.append({
                    'time': str(row['datetime']),
                    'type': event_type,
                    'size': float(row['size']),
                    'price': float(row['price']),
                    'remaining_after': remaining,
                })

        # 每个事件时刻的队列位置/身前身后量（引擎只读调用，事件数通常很少）
        for ev in events:
            time_part = ev['time'].split(' ')[-1]
            pos = self._queue_position_at(time_part, order_id)
            ev['queue'] = pos  # 不在盘口（已终结/集合竞价）时为 None

        # 汇总
        filled = sum(e['size'] for e in events if e['type'] == 'trade')
        cancelled = sum(e['size'] for e in events if e['type'] == 'cancel')
        total = float(born_row['size'])
        create_ts = pd.Timestamp(events[0]['time'])
        trades = [e for e in events if e['type'] == 'trade']
        if remaining <= 0 and filled >= total - 1e-6:
            outcome = '全部成交'
        elif remaining <= 0 and cancelled > 0:
            outcome = '部分成交后撤单' if filled > 0 else '全部撤单'
        else:
            outcome = '收盘残留'

        # 收盘残留订单没有真实的终结事件，使用当日收盘时刻作为生命周期终点。
        # 成交/撤单订单仍使用最后一条真实事件，避免改变原有统计口径。
        end_ts = (
            pd.Timestamp(f'{self.date} 15:00:00.000')
            if outcome == '收盘残留'
            else pd.Timestamp(events[-1]['time'])
        )
        summary = {
            'order_id': order_id,
            'side': int(born_row['side']),
            'price': float(born_row['price']),
            'size': total,
            'create_time': str(born_row['datetime']),
            'filled_size': filled,
            'cancelled_size': cancelled,
            'outcome': outcome,
            'lifespan_ms': int((end_ts - create_ts).total_seconds() * 1000),
            'first_fill_delay_ms': int((pd.Timestamp(trades[0]['time']) - create_ts).total_seconds() * 1000) if trades else None,
        }
        return {"success": True, "summary": summary, "events": events}

    def __str__(self) -> str:
        return f"TradeBook({self.symbol}_{self.date}, last_accessed={self.last_accessed_at})"

    def __repr__(self) -> str:
        return self.__str__()
