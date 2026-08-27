#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WangCai Trading System Python API 使用示例
"""

import pywangcai_orderbook as wc
import sys

def main():
    if len(sys.argv) != 4:
        print("用法: python example.py <symbol> <date> <data_path>")
        print("示例: python example.py 000001.SZ 2024-01-15 ./data")
        return
    
    symbol = sys.argv[1]
    date = sys.argv[2]
    data_path = sys.argv[3]
    # python3 ./test.py "000027.SZ" "2022-01-07" "./logs" 
    try:
        # 创建交易可视化器
        print(f"创建交易可视化器: {symbol} {date}")
        visualizer = wc.TradingVisualizer(symbol, date, data_path)
        
        # 运行数据处理
        print("正在处理交易数据...")
        visualizer.run()
        
        # 获取基础信息
        total_snapshots = visualizer.get_total_snapshots()
        total_changes = visualizer.get_total_changes()
        time_range = visualizer.get_time_range()
        
        print(f"\n数据处理完成:")
        print(f"  总快照数: {total_snapshots}")
        print(f"  总变化数: {total_changes}")
        if time_range:
            print(f"  时间范围: {time_range.get('start_time', 'N/A')} - {time_range.get('end_time', 'N/A')}")
        
        # 交互式查询
        interactive_query(visualizer, date, total_snapshots, total_changes)
        
    except Exception as e:
        print(f"错误: {e}")
        return 1

def interactive_query(visualizer, date, total_snapshots, total_changes):
    """交互式查询界面"""
    
    while True:
        print("\n" + "="*50)
        print("交易快照查询系统")
        print("="*50)
        print("选择查询方式:")
        print("  t - 按时间查询 (格式: HH:MM:SS)")
        print("  i - 按快照ID查询 (1 - {})".format(total_snapshots))
        print("  c - 按变化索引查询 (1 - {})".format(total_changes))
        print("  q - 退出")
        print("-"*50)
        
        choice = input("请输入选择: ").strip().lower()
        
        if choice == 'q':
            print("再见!")
            break
        elif choice == 't':
            time_str = input(f"请输入时间 (09:25:00 - 15:00:00): ").strip()
            result = visualizer.query_by_time(date, time_str)
        elif choice == 'i':
            try:
                snapshot_id = int(input(f"请输入快照ID (1 - {total_snapshots}): ").strip())
                result = visualizer.query_by_id(snapshot_id)
            except ValueError:
                print("❌ 请输入有效的数字")
                continue
        elif choice == 'c':
            try:
                change_index = int(input(f"请输入变化索引 (1 - {total_changes}): ").strip())
                result = visualizer.query_by_change_index(change_index)
            except ValueError:
                print("❌ 请输入有效的数字")
                continue
        else:
            print("❌ 无效选择，请重新输入")
            continue
        
        # 显示查询结果
        display_snapshot_result(result)

def display_snapshot_result(result):
    """显示快照查询结果"""
    
    if not result:
        print("❌ 未找到相应的快照数据")
        return
    
    # 基础信息
    print(f"\n📊 快照信息:")
    print(f"  快照ID: {result['snapshot_id']}")
    print(f"  时间戳: {result['timestamp']}")
    print(f"  变化索引: {result['change_index']}")
    
    # 市场数据
    market_data = result['market_data']
    bid1, bid2, bid3 = market_data['best_bids']
    ask1, ask2, ask3 = market_data['best_asks']
    
    print(f"\n📈 买卖档位:")
    print(f"  卖三: {wc.format_price(ask3):.4f}")
    print(f"  卖二: {wc.format_price(ask2):.4f}")
    print(f"  卖一: {wc.format_price(ask1):.4f}")
    print(f"  买一: {wc.format_price(bid1):.4f}")
    print(f"  买二: {wc.format_price(bid2):.4f}")
    print(f"  买三: {wc.format_price(bid3):.4f}")
    
    print(f"\n📊 统计信息:")
    print(f"  买一挂单量: {market_data['bid_create_count']}")
    print(f"  买一撤单量: {market_data['bid_cancel_count']}")
    print(f"  买一成交量: {market_data['bid_traded_count']}")
    print(f"  卖一挂单量: {market_data['ask_create_count']}")
    print(f"  卖一撤单量: {market_data['ask_cancel_count']}")
    print(f"  卖一成交量: {market_data['ask_traded_count']}")
    
    # 各档位详细信息
    levels = result['levels']
    level_names = ['ask3', 'ask2', 'ask1', 'bid1', 'bid2', 'bid3']
    level_labels = ['卖三', '卖二', '卖一', '买一', '买二', '买三']
    
    print(f"\n📋 各档位详细订单:")
    for level_name, label in zip(level_names, level_labels):
        level_data = levels[level_name]
        orders = level_data['orders']
        
        if len(orders) > 0:
            print(f"  {label}: {len(orders)}个订单, 总量: {level_data['total_volume']}股")
            
            # 显示前5个订单的详情
            display_count = min(5, len(orders))
            for i in range(display_count):
                order = orders[i]
                print(f"    ({order['order_local_id']}) {order['remaining_volume']}股 {order['direction']}")
            
            if len(orders) > 5:
                print(f"    ... 还有{len(orders) - 5}个订单")
        else:
            print(f"  {label}: 无订单")

def demo_programmatic_usage():
    """演示编程式使用方法"""
    
    # 创建可视化器
    visualizer = wc.TradingVisualizer("000001.SZ", "2024-01-15", "./data")
    visualizer.run()
    
    # 批量查询示例
    times_to_query = ["09:25:00", "10:00:00", "14:00:00", "15:00:00"]
    
    for time_str in times_to_query:
        result = visualizer.query_by_time("2024-01-15", time_str)
        if result:
            market_data = result['market_data']
            bid1, _, _ = market_data['best_bids']
            ask1, _, _ = market_data['best_asks']
            
            print(f"{time_str}: 买一={wc.format_price(bid1):.4f}, 卖一={wc.format_price(ask1):.4f}")
    
    # 查找特定变化
    for change_idx in range(1, min(10, visualizer.get_total_changes() + 1)):
        result = visualizer.query_by_change_index(change_idx)
        if result:
            print(f"变化{change_idx}: 时间={result['timestamp']}, 快照ID={result['snapshot_id']}")

if __name__ == "__main__":
    main()