#!/usr/bin/env python3
"""
WebSocket路由
处理实时进度通知
"""

import json
import uuid
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
from ordervis_server.utils.progress_manager import progress_manager

router = APIRouter()

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
    
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
    
    async def send_personal_message(self, message: dict, connection_id: str):
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception:
                # 连接可能已断开，移除连接
                self.disconnect(connection_id)
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection_id)
        
        # 清理断开的连接
        for connection_id in disconnected:
            self.disconnect(connection_id)

# 全局连接管理器
manager = ConnectionManager()

@router.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """WebSocket连接，用于接收特定任务的进度更新"""
    connection_id = str(uuid.uuid4())
    heartbeat_task = None
    
    try:
        await manager.connect(websocket, connection_id)
        
        # 注册WebSocket连接
        progress_manager.register_websocket(task_id, connection_id)
        
        # 发送当前任务状态
        task_info = progress_manager.get_task_info(task_id)
        if task_info:
            await manager.send_personal_message({
                "type": "task_info",
                "data": task_info
            }, connection_id)
        
        # 启动心跳任务
        heartbeat_task = asyncio.create_task(heartbeat_loop(connection_id))
        
        # 保持连接直到客户端断开
        while True:
            try:
                # 等待客户端消息（心跳或命令）
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }, connection_id)
                elif message.get("type") == "pong":
                    # 客户端响应了我们的ping，连接正常
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                # 发送错误消息
                try:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": str(e)
                    }, connection_id)
                except:
                    pass
                break
                
    except Exception as e:
        # 处理连接错误
        pass
    finally:
        # 取消心跳任务
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        # 清理连接
        progress_manager.unregister_websocket(task_id, connection_id)
        manager.disconnect(connection_id)

async def heartbeat_loop(connection_id: str):
    """心跳循环，每30秒发送一次ping"""
    while True:
        try:
            await asyncio.sleep(30)  # 30秒间隔
            await manager.send_personal_message({
                "type": "ping",
                "timestamp": asyncio.get_event_loop().time()
            }, connection_id)
        except asyncio.CancelledError:
            break
        except Exception:
            # 连接可能已断开，退出循环
            break


