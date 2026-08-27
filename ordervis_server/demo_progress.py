#!/usr/bin/env python3
"""
前端进度条演示 - 简洁版
展示如何调用 init_tradebook 接口并获取实时进度
"""

import asyncio
import aiohttp
import websockets
import json
from datetime import datetime

class ProgressDemo:
    def __init__(self, base_url="http://localhost:18080"):
        self.base_url = base_url
        self.session = None
        
    async def init_tradebook(self, symbol, date):
        """调用初始化接口"""
        url = f"{self.base_url}/tradebook/init_tradebook"
        params = {"sym": symbol, "date": date}
        
        async with self.session.post(url, params=params) as response:
            result = await response.json()
            if result.get("code") == 0:
                return result.get("data", {}).get("task_id")
            return None
    
    async def get_progress(self, task_id):
        """查询进度"""
        url = f"{self.base_url}/progress/{task_id}"
        async with self.session.get(url) as response:
            return await response.json()
    
    async def listen_progress(self, task_id):
        """监听WebSocket进度更新"""
        ws_url = f"ws://localhost:18080/ws/progress/{task_id}"
        
        # 禁用内置ping，使用自定义心跳
        kwargs = {'ping_interval': None, 'ping_timeout': None, 'close_timeout': 10}
        
        async with websockets.connect(ws_url, **kwargs) as websocket:
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "task_info":
                        self.draw_progress(data["data"]["progress"], data["data"]["message"])
                    elif msg_type == "task_completed":
                        self.draw_progress(100, "完成")
                        break
                    elif msg_type == "ping":
                        await websocket.send(json.dumps({"type": "pong", "timestamp": data.get("timestamp")}))
                        
                except asyncio.TimeoutError:
                    # 超时时查询进度作为备选方案
                    try:
                        result = await self.get_progress(task_id)
                        if result and result.get("code") == 0:
                            data = result["data"]
                            self.draw_progress(data["progress"], data["message"])
                            if data["status"] in ["completed", "failed"]:
                                break
                    except:
                        pass  # 忽略查询失败
                        
                except (websockets.exceptions.ConnectionClosedError, Exception):
                    print(f"\n❌ WebSocket连接异常")
                    break
                    
    def draw_progress(self, progress, message):
        """绘制进度条"""
        bar_width = 40
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\r[{timestamp}] [{bar}] {progress:3d}% | {message}", end="", flush=True)
        if progress >= 100:
            print()
    
    async def run(self, symbol="002131.SZ", date="20250819"):
        """运行演示"""
        self.session = aiohttp.ClientSession()
        
        try:
            # 1. 调用初始化接口
            print(f"🚀 初始化: {symbol}_{date}")
            task_id = await self.init_tradebook(symbol, date)
            
            if not task_id:
                print("❌ 初始化失败或已存在")
                return
            
            print(f"✅ 任务ID: {task_id}")
            
            # 2. 监听进度更新
            print("\n📊 监听进度更新:")
            await self.listen_progress(task_id)
            
            print("\n🎯 完成！")
            
        finally:
            await self.session.close()

async def main():
    demo = ProgressDemo()
    await demo.run()

if __name__ == "__main__":
    asyncio.run(main())
