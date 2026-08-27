#!/usr/bin/env python3
"""
TradeBook功能演示和测试脚本
展示如何使用共享存储和API接口
"""

import time
import requests
import jwt
from datetime import datetime, timedelta

# API配置
BASE_URL = "http://localhost:18080"
TEST_SECRET_KEY = "your-secret-key"  # 请根据实际配置修改
TEST_ALGORITHM = "HS256"

def generate_test_token():
    """生成测试JWT token"""
    payload = {
        "user_id": "demo_user",
        "username": "tradebook_demo",
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)

def test_date_list():
    """测试获取交易日列表"""
    print("\n📅 测试获取交易日列表...")
    try:
        response = requests.get(f"{BASE_URL}/tradebook/DateList")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                date_list = data['data']
                print(f"   ✅ 获取成功，共 {len(date_list)} 个交易日")
                if date_list:
                    print(f"   最新交易日: {date_list[0]}")
                    print(f"   最早交易日: {date_list[-1]}")
                return True
            else:
                print(f"   ❌ API返回失败: {data.get('message')}")
                return False
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

def test_sym_list():
    """测试获取标的列表"""
    print("\n📈 测试获取标的列表...")
    try:
        response = requests.get(f"{BASE_URL}/tradebook/symList")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                sym_list = data['data']
                print(f"   ✅ 获取成功，共 {len(sym_list)} 个标的")
                if sym_list:
                    print(f"   示例标的: {sym_list[:5]}")  # 显示前5个标的
                return True
            else:
                print(f"   ❌ API返回失败: {data.get('message')}")
                return False
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

def demo_api_calls():
    """演示API调用"""
    print("\n🌐 API调用演示")
    print("="*50)
    
    try:
        # 生成token
        token = generate_test_token()
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 生成测试token")
        
        # 测试数据
        test_symbol = "000027.SZ"
        test_date = "2025-08-01"
        
        # 测试快照摘要
        print(f"\n📊 获取 {test_symbol}_{test_date} 摘要...")
        params = {"sym": test_symbol, "date": test_date}
        response = requests.get(f"{BASE_URL}/tradebook/snapshots_summary", 
                              params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                summary = data['data']
                print(f"   ✅ 获取成功")
                print(f"   总快照数: {summary.get('total_snapshots', 0)}")
                print(f"   总变化数: {summary.get('total_changes', 0)}")
                print(f"   时间范围: {summary.get('time_range', 'N/A')}")
            else:
                print(f"   ⚠️  API返回失败: {data.get('message')}")
        elif response.status_code == 401:
            print(f"   ❌ 认证失败，请检查JWT配置")
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
        
        # 测试快照查询
        print(f"\n🕒 测试时间查询...")
        params = {"sym": test_symbol, "date": test_date, "time": "09:31:30.000"}
        response = requests.get(f"{BASE_URL}/tradebook/snapshot_by_time", 
                              params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                print(f"   ✅ 时间查询成功")
                snapshot = data['data'].get('snapshot')
                if snapshot:
                    print(f"   快照数据类型: {type(snapshot)}")
                    print(f"   数据大小: {len(str(snapshot))} 字符")
            else:
                print(f"   ⚠️  未找到数据: {data.get('message')}")
        else:
            print(f"   状态码: {response.status_code}")
        
        # 测试ID查询
        print(f"\n🆔 测试ID查询...")
        params = {"sym": test_symbol, "date": test_date, "id": 100}
        response = requests.get(f"{BASE_URL}/tradebook/snapshot_by_id", 
                              params=params, headers=headers)
        
        print(f"   ID查询状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   查询结果: {data.get('code') == 0}")
        
        # 测试索引查询
        print(f"\n📋 测试索引查询...")
        params = {"sym": test_symbol, "date": test_date, "index": 0}
        response = requests.get(f"{BASE_URL}/tradebook/snapshot_by_index", 
                              params=params, headers=headers)
        
        print(f"   索引查询状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   查询结果: {data.get('code') == 0}")
        
        # 测试订单统计信息
        print(f"\n📈 测试订单统计信息...")
        params = {"sym": test_symbol, "date": test_date, "time": "09:31:30.000"}
        response = requests.get(f"{BASE_URL}/tradebook/pastTimeTradeInfo", 
                              params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                print(f"   ✅ 订单统计信息获取成功")
                trade_info = data['data']
                print(trade_info)
            else:
                print(f"   ❌ 获取失败: {data.get('message')}")
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API调用演示失败: {e}")
        return False


def main():
    """主演示函数"""
    print("🎯 TradeBook功能演示")
    print("="*60)
    print(f"🕒 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    try:
        # 1. 测试基础API接口
        print("🔧 测试基础API接口")
        print("-" * 30)
        
        if test_date_list():
            print("✅ 交易日列表测试通过")
        else:
            print("❌ 交易日列表测试失败")
        
        if test_sym_list():
            print("✅ 标的列表测试通过")
        else:
            print("❌ 标的列表测试失败")
        
        time.sleep(1)
        
        # 2. 测试订单统计信息接口
        print("\n📈 测试订单统计信息接口")
        print("-" * 30)
        
        time.sleep(1)
        
        # 3. API调用演示
        if demo_api_calls():
            print("\n✅ API调用演示完成")
        else:
            print("\n❌ API调用演示失败")
        
        time.sleep(1)
        
        
        # 4. 清理选项
        print("\n" + "="*60)
        
        print("\n🎉 演示完成！")
        print("💡 提示:")
        print("   • 修改 TEST_SECRET_KEY 以匹配你的JWT配置")
        print("   • 所有API现在使用统一的 {code, data, message} 响应格式")
        print("   • code=0 表示成功，code=1 表示失败")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")

if __name__ == "__main__":
    main()