#!/usr/bin/env python3
"""
adata 到 aqdatac 格式转换工具
将 adata 返回的数据格式转换为 aqdatac 兼容格式
"""
import pandas as pd
import adata


def convert_bytes_to_str(value):
    """将 bytes 类型转换为字符串"""
    if isinstance(value, bytes):
        decoded = value.decode('utf-8').strip()
        return decoded if decoded else '0'
    elif pd.isna(value) or value == '':
        return '0'
    else:
        return str(value)


def get_csord_ad(date_str, sym):
    """
    获取 csord 数据并转换为 aqdatac 格式
    
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD
        sym: 股票代码，如 '000027.SZ'
    
    Returns:
        DataFrame: aqdatac 格式的 csord 数据
    
    Raises:
        ValueError: 当数据获取失败或数据为空时
    """
    csord = adata.get_data('csord', date_str, date_str, [sym])
    
    # 验证返回的数据
    if not isinstance(csord, pd.DataFrame):
        raise ValueError(f"adata.get_data 返回了非 DataFrame 对象: {type(csord)}")
    
    if csord.empty:
        raise ValueError(f"csord 数据为空: {sym} {date_str}")
    
    # 创建 datetime 列
    csord['datetime'] = csord['date'] + pd.to_timedelta(csord['time'])
    
    # 设置索引
    csord.set_index('datetime', inplace=True, drop=False)
    
    # 选择需要的列（与 aqdatac 格式一致）
    ord_cols = ["datetime", "sym", "price", "size", "side", "ordertype", 
                "orderid", "channelno", "seqno", "bizindex"]
    
    return csord[ord_cols]


def get_cstra_ad(date_str, sym):
    """
    获取 cstra 数据并转换为 aqdatac 格式
    
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD
        sym: 股票代码，如 '000027.SZ'
    
    Returns:
        DataFrame: aqdatac 格式的 cstra 数据
    
    Raises:
        ValueError: 当数据获取失败或数据为空时
    """
    cstra = adata.get_data('cstra', date_str, date_str, [sym])
    
    # 验证返回的数据
    if not isinstance(cstra, pd.DataFrame):
        raise ValueError(f"adata.get_data 返回了非 DataFrame 对象: {type(cstra)}")
    
    if cstra.empty:
        raise ValueError(f"cstra 数据为空: {sym} {date_str}")
    
    # 创建 datetime 列
    cstra['datetime'] = cstra['date'] + pd.to_timedelta(cstra['time'])
    
    # 转换 exectype 和 tradebsflag 从 bytes 到字符串
    cstra['exectype'] = cstra['exectype'].apply(convert_bytes_to_str)
    cstra['tradebsflag'] = cstra['tradebsflag'].apply(convert_bytes_to_str)
    
    # 设置索引
    cstra.set_index('datetime', inplace=True, drop=False)
    
    # 选择需要的列（与 aqdatac 格式一致）
    tra_cols = ["datetime", "sym", "price", "size", "bidorderid", "askorderid", 
                "tradeid", "exectype", "tradebsflag", "channelno", "bizindex"]
    
    return cstra[tra_cols]


def get_cstick_ad(date_str, sym):
    """
    获取 cstick 数据并转换为 aqdatac 格式
    
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD
        sym: 股票代码，如 '000027.SZ'
    
    Returns:
        DataFrame: aqdatac 格式的 cstick 数据
    
    Raises:
        ValueError: 当数据获取失败或数据为空时
    """
    cstick = adata.get_data('cstick', date_str, date_str, [sym])
    
    # 验证返回的数据
    if not isinstance(cstick, pd.DataFrame):
        raise ValueError(f"adata.get_data 返回了非 DataFrame 对象: {type(cstick)}")
    
    if cstick.empty:
        raise ValueError(f"cstick 数据为空: {sym} {date_str}")
    
    # 创建 datetime 列
    cstick['datetime'] = cstick['date'] + pd.to_timedelta(cstick['time'])
    
    # 设置索引
    cstick.set_index('datetime', inplace=True, drop=False)
    
    # adata 只提供 bid1-bid5 和 ask1-ask5
    # aqdatac 格式需要 bid1-bid10 和 ask1-ask10
    # 补充缺失的列（bid6-bid10, ask6-ask10）并填充为 0
    for i in range(6, 11):
        cstick[f'bid{i}'] = 0.0
        cstick[f'bsize{i}'] = 0.0
        cstick[f'ask{i}'] = 0.0
        cstick[f'asize{i}'] = 0.0
    
    # 选择需要的列（与 aqdatac 格式一致，包括 bid/ask 1-10）
    aq_cols = [
        'datetime', 'sym', 'prevclose', 'open', 'high', 'low', 'close', 
        'volume', 'turnover', 'tradecount',
        'bid1', 'bsize1', 'bid2', 'bsize2', 'bid3', 'bsize3', 'bid4', 'bsize4', 
        'bid5', 'bsize5', 'bid6', 'bsize6', 'bid7', 'bsize7', 'bid8', 'bsize8', 
        'bid9', 'bsize9', 'bid10', 'bsize10',
        'ask1', 'asize1', 'ask2', 'asize2', 'ask3', 'asize3', 'ask4', 'asize4', 
        'ask5', 'asize5', 'ask6', 'asize6', 'ask7', 'asize7', 'ask8', 'asize8', 
        'ask9', 'asize9', 'ask10', 'asize10',
        'avgbid', 'avgask', 'totalbsize', 'totalasize', 'iopv'
    ]
    
    return cstick[aq_cols]


def save_to_csv(df, filepath):
    """
    保存 DataFrame 到 CSV 文件
    
    Args:
        df: DataFrame 对象
        filepath: 保存路径
    """
    # 重置索引，确保 datetime 列作为普通列保存
    df_to_save = df.reset_index(drop=True)
    df_to_save.to_csv(filepath, index=False)


if __name__ == "__main__":
    # 测试代码
    import os
    
    # 登录
    username = os.getenv("aq_username")
    password = os.getenv("aq_password")
    if not username or not password:
        raise RuntimeError("aq_username and aq_password must be set")
    adata.login(username, password)
    
    # 测试参数
    test_date = "2022-01-10"
    test_sym = "000027.SZ"
    
    print("测试转换函数...")
    
    # 测试 csord
    csord = get_csord_ad(test_date, test_sym)
    print(f"\n✅ csord 转换成功，shape: {csord.shape}")
    
    # 测试 cstra
    cstra = get_cstra_ad(test_date, test_sym)
    print(f"✅ cstra 转换成功，shape: {cstra.shape}")
    print(f"   exectype 类型: {cstra['exectype'].dtype}")
    print(f"   tradebsflag 类型: {cstra['tradebsflag'].dtype}")
    
    # 测试 cstick
    cstick = get_cstick_ad(test_date, test_sym)
    print(f"✅ cstick 转换成功，shape: {cstick.shape}")
    print(f"   列数: {len(cstick.columns)}")
