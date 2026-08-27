import pandas as pd
import adata
import os


def login_aqdatac():
    """登录aqdatac"""
    username = os.getenv("aq_username")
    password = os.getenv("aq_password")
    if not username or not password:
        raise RuntimeError("aq_username and aq_password must be set")
    adata.login(username, password)
    print("登录成功")

def findOrder(orders, order_time, order_price, order_size, order_side, tolerance_ms=100):
    '''
    根据订单时间、价格、数量和方向查找订单（使用pandas矢量化计算加速）
    input:
        orders: pandas DataFrame，包含 'orderid', 'datetime', 'price', 'size', 'side' 列
        order_time: 订单时间
        order_price: 订单价格
        order_size: 订单数量
        order_side: 订单方向（1为买，-1为卖）
        tolerance_ms: 时间容差，单位为毫秒，默认100ms

    return:
        success: 是否找到订单
        orderid: 找到的订单ID，未找到则为None
        datetime: 找到的订单时间，未找到则为None
    '''

    try:
        # 将时间转换为 pd.Timestamp
        if isinstance(order_time, str):
            order_time = pd.Timestamp(order_time)

        if len(orders) == 0:
            return False, None, None

        # 矢量化计算：价格、数量和方向的匹配
        price_match = (orders['price'] - order_price).abs() < 1e-6
        size_match = (orders['size'] - order_size).abs() < 1e-6
        side_match = orders['side'] == order_side
        combined_match = price_match & size_match & side_match

        # 第一步：查找时间大于等于给定时间的匹配订单
        time_forward_match = orders['datetime'] >= order_time
        forward_matches = orders[combined_match & time_forward_match]

        if len(forward_matches) > 0:
            # 选择时间最早的订单，如果有多个相同时间的订单，取第一个
            min_time = forward_matches['datetime'].min()
            first_match = forward_matches[forward_matches['datetime'] == min_time].iloc[0]
            return True, first_match['orderid'], first_match['datetime']

        # 第二步：向前查找容差时间内最接近下单时间的订单
        time_diff = order_time - orders['datetime']
        time_backward_match = (orders['datetime'] < order_time) & (time_diff < pd.Timedelta(f"{tolerance_ms}ms"))
        backward_matches = orders[combined_match & time_backward_match]

        if len(backward_matches) > 0:
            # 选择时间最接近的订单（时间最大），如果有多个相同时间的订单，取第一个
            max_time = backward_matches['datetime'].max()
            first_match = backward_matches[backward_matches['datetime'] == max_time].iloc[0]
            return True, first_match['orderid'], first_match['datetime']

        # 未找到匹配订单
        return False, None, None

    except Exception as e:
        print(f"查找订单时发生错误: {e}")
        return False, None, None

if __name__ == '__main__':
    login_aqdatac()
    orders = adata.get_data("csord", '2025-02-17', '2025-02-17', ['600050.SH'])
    print(orders)
    order_time = '2025-02-17 14:59:59.730'  # 需要包含完整的日期和时间
    order_price = 6.52
    order_size = 2000.0
    order_side = 1  # 1为买单，-1为卖单

    # 测试：匹配side
    success, orderid, time = findOrder(orders, order_time, order_price, order_size, order_side)
    print(f"匹配side={order_side}: {success}, orderid={orderid}, time={time}")
