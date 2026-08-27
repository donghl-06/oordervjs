

import lib.pywangcai_orderbook as wc
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable, Union
from threading import Lock
import os
import adata

class TradeBook:
    def __init__(self, symbol: str, date: str, data_path: str = "./data/", progress_callback: Optional[Callable] = None, is_ETF: bool = False):
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

    @classmethod
    def create_with_progress(cls, symbol: str, date: str, data_path: str = "./data/", progress_callback: Optional[Callable] = None, is_ETF: bool = False):
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
        return self.visualizer.query_by_time(self.date, time)
    
    def get_snapshot_by_id(self, id: int):
        """按照id查询快照"""
        self.update_access_time()
        return self.visualizer.query_by_id(id)
    
    def get_snapshot_by_index(self, index: int):
        """按照索引查询快照"""
        self.update_access_time()
        return self.visualizer.query_by_change_index(index)

    def get_market_data(self, time: str):
        """获取市场数据"""
        self.update_access_time()
        return self.visualizer.query_market_data(self.date, time)

    def get_idle_time(self) -> timedelta:
        """获取空闲时间"""
        return datetime.now() - self.last_accessed_at
    
    def get_orders_data(self):
        """获取订单数据 (用于find_order功能)"""
        try:
            # 按照 example.py 的方式，使用 adata.get_data()
            return adata.get_data("csord", self.date, self.date, [self.symbol])
        except Exception as e:
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

            # 转换时间
            if isinstance(order_time, str):
                target_time = pd.Timestamp(order_time)
            else:
                target_time = order_time

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

    def __str__(self) -> str:
        return f"TradeBook({self.symbol}_{self.date}, last_accessed={self.last_accessed_at})"

    def __repr__(self) -> str:
        return self.__str__()
