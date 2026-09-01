#!/usr/bin/env python3
"""
TradeBook路由
提供TradeBook相关的API接口
"""
import os
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import datetime as dt
from ordervis_server.utils.shared_storage import get_shared_storage, is_orderbook_fund_code
from ordervis_server.utils.tradebook import TradeBook
from ordervis_server.utils.auth import get_current_user
from ordervis_server.utils.utils import get_data_sqlserver, subtract_milliseconds

router = APIRouter(prefix="/tradebook", tags=["TradeBook"])

@router.get("/DateList", summary="获取交易日列表")
async def dateList(
    # current_user: dict = Depends(get_current_user)
):
    try:
        current_date = dt.datetime.now().strftime("%Y%m%d")
        sql = f'''
            SELECT distinct CONVERT(varchar, CONVERT(date, TRADE_DAYS), 23) as date  FROM  Filesync.dbo.AShareCalendar 
            where trade_days > '20190101' and trade_days <= '{current_date}' 
            order by date desc
        '''
        data = get_data_sqlserver(sql)

        return {
            "code": 0,
            "data": data['date'].tolist(),
            "message": "获取交易日列表成功"
        }
    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取交易日列表失败: {str(e)}"
        }
    
@router.get("/symList", summary="获取标的列表")
async def symList(
    # current_user: dict = Depends(get_current_user)
):
    try:
        current_date = dt.datetime.now().strftime("%Y%m%d")

        # 获取股票基本信息
        stock_sql = f"""
            SELECT S_INFO_WINDCODE as code
            FROM Filesync.dbo.asharedescription
            WHERE
                (S_INFO_LISTDATE IS NULL OR S_INFO_LISTDATE = '' OR S_INFO_LISTDATE <= '{current_date}')
                AND (S_INFO_DELISTDATE IS NULL OR S_INFO_DELISTDATE = '' OR S_INFO_DELISTDATE > '{current_date}')
        """
        stock_data = get_data_sqlserver(stock_sql)
        stock_codes = stock_data['code'].tolist() if not stock_data.empty else []

        # 获取基金基本信息。场外基金（.OF）没有订单簿数据，不纳入本页面的可回放标的。
        fund_sql = f"""
            SELECT F_INFO_WINDCODE as code
            FROM Filesync.dbo.chinamutualfunddescription
            WHERE
                (F_INFO_LISTDATE IS NULL OR F_INFO_LISTDATE = '' OR F_INFO_LISTDATE <= '{current_date}')
                AND (F_INFO_DELISTDATE IS NULL OR F_INFO_DELISTDATE = '' OR F_INFO_DELISTDATE > '{current_date}')
        """
        fund_data = get_data_sqlserver(fund_sql)
        fund_codes = []
        if not fund_data.empty:
            fund_codes = [
                code for code in fund_data["code"].tolist()
                if is_orderbook_fund_code(code)
            ]

        # 合并股票和基金代码
        all_codes = stock_codes + fund_codes

        # 附带证券类型（stock/fund/unknown），供前端分型筛选（D9）
        storage = get_shared_storage()
        items = [{"code": code, "type": storage.classify_symbol(code)} for code in all_codes]

        return {
            "code": 0,
            "data": items,
            "message": f"获取标的列表成功 (股票: {len(stock_codes)}个, 场内基金: {len(fund_codes)}个, 合计: {len(all_codes)}个)"
        }
    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取标的列表失败: {str(e)}"
        }

@router.get("/snapshots_summary", summary="获取快照摘要")
async def snapshots_summary(
    sym: str,
    date: str,
    # current_user: dict = Depends(get_current_user)
):
    storage = get_shared_storage()
    tradebook = storage.get(sym, date)
    
    if not tradebook:
        return {
            "code": 1,
            "data": None,
            "message": f"TradeBook {sym}_{date} 不存在"
        }
    
    try:
        # 获取基本统计信息
        total_snapshots = tradebook.get_total_snapshots()
        total_changes = tradebook.get_total_changes()
        time_range = tradebook.get_time_range()
        
        # 构建摘要响应
        summary = {
            "symbol": tradebook.symbol,
            "date": tradebook.date,
            "total_snapshots": total_snapshots,
            "total_changes": total_changes,
            "time_range": time_range,
            "is_ETF": tradebook.is_ETF
        }
        
        return {
            "code": 0,
            "data": summary,
            "message": f"获取 {sym}_{date} 快照摘要成功"
        }
        
    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取快照摘要失败: {str(e)}"
        }

@router.get("/snapshot_by_time", summary="按时间获取快照")
async def snapshot_by_time(
    sym: str,
    date: str,
    time: str,
    # current_user: dict = Depends(get_current_user)
):
    storage = get_shared_storage()
    tradebook = storage.get(sym, date)
    
    if not tradebook:
        return {
            "code": 1,
            "data": None,
            "message": f"TradeBook {sym}_{date} 不存在"
        }
    
    try:
        # 获取指定时间的快照
        snapshot_data = tradebook.get_snapshot_by_time(time)
        
        if snapshot_data is None:
            return {
                "code": 1,
                "data": None,
                "message": f"未找到 {sym}_{date} 在时间 {time} 的快照数据"
            }
        
        return {
            "code": 0,
            "data": {
                "symbol": sym,
                "date": date,
                "time": time,
                "snapshot": snapshot_data,
                "is_ETF": tradebook.is_ETF
            },
            "message": f"获取 {sym}_{date} 时间 {time} 的快照成功"
        }
        
    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取快照失败: {str(e)}"
        }

@router.get("/snapshot_by_id", summary="按ID获取快照")
async def snapshot_by_id(
    sym: str,
    date: str,
    id: int,
    # current_user: dict = Depends(get_current_user)
):
    storage = get_shared_storage()
    tradebook = storage.get(sym, date)
    
    if not tradebook:
        return {
            "code": 1,
            "data": None,
            "message": f"TradeBook {sym}_{date} 不存在"
        }
    
    try:
        # 获取指定ID的快照
        snapshot_data = tradebook.get_snapshot_by_id(id)
        
        if snapshot_data is None:
            return {
                "code": 1,
                "data": None,
                "message": f"未找到 {sym}_{date} ID为 {id} 的快照数据"
            }
        
        return {
            "code": 0,
            "data": {
                "symbol": sym,
                "date": date,
                "id": id,
                "snapshot": snapshot_data,
                "is_ETF": tradebook.is_ETF
            },
            "message": f"获取 {sym}_{date} ID {id} 的快照成功"
        }
        
    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取快照失败: {str(e)}"
        }

@router.get("/snapshot_by_index", summary="按索引获取快照")
async def snapshot_by_index(
    sym: str,
    date: str,
    index: int,
    # current_user: dict = Depends(get_current_user)
):
    storage = get_shared_storage()
    tradebook = storage.get(sym, date)
    
    if not tradebook:
        return {
            "code": 1,
            "data": None,
            "message": f"TradeBook {sym}_{date} 不存在"
        }
    
    try:
        # 获取指定索引的快照
        snapshot_data = tradebook.get_snapshot_by_index(index)
        
        if snapshot_data is None:
            return {
                "code": 1,
                "data": None,
                "message": f"未找到 {sym}_{date} 索引为 {index} 的快照数据"
            }
        
        return {
            "code": 0,
            "data": {
                "symbol": sym,
                "date": date,
                "index": index,
                "snapshot": snapshot_data
            },
            "message": f"获取 {sym}_{date} 索引 {index} 的快照成功"
        }
        
    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取快照失败: {str(e)}"
        }

@router.get("/next_change", summary="获取相邻变化快照")
async def next_change(
    sym: str,
    date: str,
    time: str,
    direction: int = 1,
    # current_user: dict = Depends(get_current_user)
):
    """
    获取指定时间之后(direction=1)或之前(-1)第一个有变化的快照。
    用于替代前端步进时的串行轮询（A2），一次请求返回结果。
    """
    storage = get_shared_storage()
    tradebook = storage.get(sym, date)

    if not tradebook:
        return {
            "code": 1,
            "data": None,
            "message": f"TradeBook {sym}_{date} 不存在"
        }

    try:
        snapshot_data = tradebook.get_adjacent_change(time, direction)

        if snapshot_data is None:
            return {
                "code": 1,
                "data": None,
                "message": f"{sym}_{date} 在时间 {time} {'之后' if direction >= 0 else '之前'}没有更多变化"
            }

        return {
            "code": 0,
            "data": {
                "symbol": sym,
                "date": date,
                "time": time,
                "direction": direction,
                "snapshot": snapshot_data,
                "is_ETF": tradebook.is_ETF
            },
            "message": "获取相邻变化快照成功"
        }

    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取相邻变化快照失败: {str(e)}"
        }


@router.get("/trade_flow_series", summary="获取时间窗口内流量序列")
async def trade_flow_series(
    sym: str,
    date: str,
    time: str,
    window_ms: int,
    points: int = 60,
    # current_user: dict = Depends(get_current_user)
):
    """
    获取 [time-window_ms, time] 窗口内买一/卖一的挂单/撤单/成交量分桶序列（C2 图表数据）。
    挂单量字段为 bid_volume/ask_volume，并附带桶右缘的 bid_price/ask_price；撤单和成交曲线使用日内累计字段，并附带桶内 trade_prices 成交价列表
    *_cancel_cumulative/*_traded_cumulative，原 *_cancel/*_traded 保留为采样桶内瞬时新增量。
    """
    storage = get_shared_storage()
    tradebook = storage.get(sym, date)

    if not tradebook:
        return {
            "code": 1,
            "data": None,
            "message": f"TradeBook {sym}_{date} 不存在"
        }

    try:
        series = tradebook.get_trade_flow_series(time, window_ms, points)

        return {
            "code": 0,
            "data": {
                "symbol": sym,
                "date": date,
                "time": time,
                "window_ms": window_ms,
                "series": series
            },
            "message": f"获取流量序列成功（{len(series)} 桶）"
        }

    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取流量序列失败: {str(e)}"
        }


@router.get("/order_lifecycle", summary="获取订单生命周期")
async def order_lifecycle(
    sym: str,
    date: str,
    order_id: int,
    # current_user: dict = Depends(get_current_user)
):
    """
    重建订单生命周期（B4）：挂出 -> 逐笔成交/撤单 -> 终结。
    order_id 为快照订单的 order_local_id（即 csord CSV 的 orderid）。
    每个事件附带该时刻的队列位置与身前/身后量（盘口外则为 null）。
    """
    storage = get_shared_storage()
    tradebook = storage.get(sym, date)

    if not tradebook:
        return {
            "code": 1,
            "data": None,
            "message": f"TradeBook {sym}_{date} 不存在"
        }

    try:
        result = tradebook.get_order_lifecycle(order_id)

        if not result.get("success"):
            return {
                "code": 1,
                "data": None,
                "message": result.get("message", "订单生命周期查询失败")
            }

        return {
            "code": 0,
            "data": {
                "symbol": sym,
                "date": date,
                "summary": result["summary"],
                "events": result["events"]
            },
            "message": "获取订单生命周期成功"
        }

    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取订单生命周期失败: {str(e)}"
        }


@router.get("/order_queue_series", summary="获取锁定订单队列序列")
async def order_queue_series(
    sym: str,
    date: str,
    time: str,
    window_ms: int,
    order_ids: str,
    points: int = 60,
    # current_user: dict = Depends(get_current_user)
):
    """
    获取窗口内锁定订单的身前/身后量序列。
    order_ids 使用逗号分隔，例如：123,456,789。
    每个时间点对应一次盘口快照；订单不在盘口中时返回 null。
    """
    storage = get_shared_storage()
    tradebook = storage.get(sym, date)

    if not tradebook:
        return {
            "code": 1,
            "data": None,
            "message": f"TradeBook {sym}_{date} 不存在"
        }

    try:
        parsed_ids = []
        for raw_id in order_ids.split(','):
            raw_id = raw_id.strip()
            if not raw_id:
                continue
            parsed_ids.append(int(raw_id))
        parsed_ids = list(dict.fromkeys(parsed_ids))
        if not parsed_ids:
            return {
                "code": 1,
                "data": None,
                "message": "order_ids 不能为空"
            }

        series = tradebook.get_order_queue_series(time, window_ms, parsed_ids, points)
        return {
            "code": 0,
            "data": {
                "symbol": sym,
                "date": date,
                "time": time,
                "window_ms": window_ms,
                "order_ids": parsed_ids,
                "series": series,
            },
            "message": f"获取锁定订单队列序列成功（{len(series)} 个采样点）"
        }
    except ValueError:
        return {
            "code": 1,
            "data": None,
            "message": "order_ids 必须是逗号分隔的整数"
        }
    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取锁定订单队列序列失败: {str(e)}"
        }


@router.get("/pastTimeTradeInfo", summary="获取订单统计信息")
async def pastTimeTradeInfo(
    sym: str,
    date: str,
    time: str,
    # current_user: dict = Depends(get_current_user)
):
    storage = get_shared_storage()
    tradebook = storage.get(sym, date)
    
    if not tradebook:
        return {
            "code": 1,
            "data": None,
            "message": f"TradeBook {sym}_{date} 不存在"
        }
    
    try:
        # 定义时间间隔和对应的键名
        time_intervals = {
            "last_1min": 60 * 1000,
            "last_3s": 3 * 1000,
            "last_500ms": 500,
            "last_50ms": 50,
            "last_10ms": 10
        }
        
        # 定义指标名称
        metrics = ['买一新增撤单', '买一新增挂单', '买一新增成交', '卖一新增撤单', '卖一新增挂单', '卖一新增成交']
        
        # 定义市场数据字段映射
        field_mapping = [
            'bid_cancel_count', 'bid_create_count', 'bid_traded_count',
            'ask_cancel_count', 'ask_create_count', 'ask_traded_count'
        ]
        
        # 获取当前时间快照
        current_snapshot = tradebook.get_market_data(time if time >= '09:30:00.000' else '09:30:00.000')
        current_data = current_snapshot['market_data']

        
        # 初始化结果数据结构
        result = {"level": metrics}
        
        # 批量获取历史快照
        historical_snapshots = {}
        for key, ms in time_intervals.items():
            past_time = subtract_milliseconds(time, ms)
            historical_snapshots[key] = tradebook.get_market_data(past_time if past_time >= '09:30:00.000' else '09:30:00.000')
            result[key] = []
        
        # 计算每个时间间隔的差值
        for key in time_intervals.keys():
            historical_data = historical_snapshots[key]['market_data']
            for field in field_mapping:
                diff = current_data[field] - historical_data[field]
                result[key].append(diff)

        # 修补撤单指标：引擎撤单计数器恒为0，改用 CSV 重算（买一/卖一撤单量）
        # result[key] 的索引 0=买一新增撤单, 3=卖一新增撤单（与 metrics/field_mapping 顺序一致）
        from ordervis_server.utils.tradebook import _time_to_ms
        end_ms = _time_to_ms(time if time >= '09:30:00.000' else '09:30:00.000')
        for key, ms in time_intervals.items():
            records = tradebook._best_level_cancel_volumes(end_ms - ms, end_ms)
            result[key][0] = sum(r['volume'] for r in records if r['side'] == 'bid')
            result[key][3] = sum(r['volume'] for r in records if r['side'] == 'ask')
        
        # 构建最终返回数据
        res_data = []
        for i, level in enumerate(metrics):
            item = {'level': level}
            for key in time_intervals.keys():
                item[key] = result[key][i]
            res_data.append(item)
    
        return {
            "code": 0,
            "data": res_data,
            "message": "获取订单统计信息成功"
        }
    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"获取订单统计信息失败: {str(e)}"
        }

@router.post("/init_tradebook", summary="异步初始化TradeBook")
async def init_tradebook(
    sym: str,
    date: str,
    # current_user: dict = Depends(get_current_user)
):
    """
    异步初始化TradeBook，返回任务ID用于进度跟踪
    """
    try:
        storage = get_shared_storage()
        task_id = storage.get_with_progress(sym, date)
        
        if task_id is None:
            # 已存在且未过期
            return {
                "code": 0,
                "data": {
                    "task_id": None,
                    "status": "ready",
                    "message": f"TradeBook {sym}_{date} 已存在且可用"
                },
                "message": "TradeBook已准备就绪"
            }
        
        return {
            "code": 0,
            "data": {
                "task_id": task_id,
                "status": "initializing",
                "message": f"开始初始化 TradeBook {sym}_{date}"
            },
            "message": "初始化任务已创建"
        }
        
    except Exception as e:
        return {
            "code": 1,
            "data": None,
            "message": f"创建初始化任务失败: {str(e)}"
        }

@router.get("/find_order", summary="根据订单条件查找订单")
async def find_order(
    sym: str,
    date: str,
    order_time: str,
    order_price: float,
    order_size: float,
    order_side: int,
    tolerance_ms: int = 100,
    # current_user: dict = Depends(get_current_user)
):
    """
    根据订单时间、价格、数量和方向查找订单
    
    参数说明：
    - sym: 交易对代码，如 '000001.SZ'
    - date: 交易日期，如 '2024-01-15'
    - order_time: 订单时间，如 '2024-01-15 14:59:59.730' 或 '14:59:59.730'
    - order_price: 订单价格
    - order_size: 订单数量
    - order_side: 订单方向（1为买单，-1为卖单）
    - tolerance_ms: 时间容差（毫秒），默认100ms
    """
    try:
        # 使用 adata_converter 获取转换后的数据，确保格式与 aqdatac 一致
        import pandas as pd
        import sys
        import os
        
        # 添加 utils 目录到路径
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        
        from ordervis_server.utils.adata_converter import get_csord_ad
        
        # 使用转换器获取数据，返回的数据已经包含 datetime 列
        try:
            orders_df = get_csord_ad(date, sym)
        except ValueError as ve:
            # 处理数据为空或格式错误的情况
            return {
                "code": 1,
                "data": None,
                "message": f"无法获取订单数据: {str(ve)}"
            }
        
        if orders_df is None or len(orders_df) == 0:
            return {
                "code": 1,
                "data": None,
                "message": "无法获取订单数据或数据为空"
            }
        
        # 转换时间格式
        if isinstance(order_time, str):
            # 如果只包含时间部分，添加日期
            if ' ' not in order_time:
                target_time = pd.Timestamp(f"{date} {order_time}")
            else:
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
            result = {
                "success": True,
                "orderid": int(first_match['orderid']),
                "datetime": str(first_match['datetime']),
                "price": float(first_match['price']),
                "size": float(first_match['size']),
                "side": int(first_match['side']),
                "message": f"成功找到匹配的订单: ID={first_match['orderid']}"
            }
        else:
            # 第二步：向前查找容差时间内最接近下单时间的订单
            time_diff = target_time - orders_df['datetime']
            time_backward_match = (orders_df['datetime'] < target_time) & (time_diff < pd.Timedelta(f"{tolerance_ms}ms"))
            backward_matches = orders_df[combined_match & time_backward_match]

            if len(backward_matches) > 0:
                # 选择时间最接近的订单
                max_time = backward_matches['datetime'].max()
                first_match = backward_matches[backward_matches['datetime'] == max_time].iloc[0]
                result = {
                    "success": True,
                    "orderid": int(first_match['orderid']),
                    "datetime": str(first_match['datetime']),
                    "price": float(first_match['price']),
                    "size": float(first_match['size']),
                    "side": int(first_match['side']),
                    "message": f"在容差时间内找到匹配的订单: ID={first_match['orderid']}"
                }
            else:
                result = {
                    "success": False,
                    "orderid": None,
                    "datetime": None,
                    "message": "没有找到匹配的订单"
                }
        
        return {
            "code": 0,
            "data": {
                "symbol": sym,
                "date": date,
                "query_params": {
                    "order_time": order_time,
                    "order_price": order_price,
                    "order_size": order_size,
                    "order_side": order_side,
                    "tolerance_ms": tolerance_ms
                },
                "result": result
            },
            "message": result.get("message", "订单查找完成")
        }
        
    except Exception as e:
        import traceback
        return {
            "code": 1,
            "data": None,
            "message": f"查找订单失败: {str(e)}",
            "traceback": traceback.format_exc()
        }