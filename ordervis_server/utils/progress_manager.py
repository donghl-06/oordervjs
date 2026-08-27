#!/usr/bin/env python3
"""
进度管理器
处理TradeBook初始化过程中的进度通知
"""

import asyncio
import json
from typing import Dict, Set, Optional, Callable
from datetime import datetime
import uuid
from threading import Lock

class ProgressManager:
    """进度管理器，用于管理多个TradeBook初始化任务的进度"""
    
    def __init__(self):
        self._tasks: Dict[str, Dict] = {}  # task_id -> task_info
        self._websocket_connections: Dict[str, Set[str]] = {}  # task_id -> set of connection_ids
        self._lock = Lock()
    
    def create_task(self, symbol: str, date: str) -> str:
        """创建新的进度任务"""
        task_id = str(uuid.uuid4())
        
        with self._lock:
            self._tasks[task_id] = {
                'id': task_id,
                'symbol': symbol,
                'date': date,
                'status': 'initializing',  # initializing, completed, failed
                'progress': 0,
                'message': '开始初始化...',
                'created_at': datetime.now().isoformat(),
                'completed_at': None,
                'error': None
            }
            self._websocket_connections[task_id] = set()
        
        return task_id
    
    def register_websocket(self, task_id: str, connection_id: str):
        """注册WebSocket连接"""
        with self._lock:
            if task_id in self._websocket_connections:
                self._websocket_connections[task_id].add(connection_id)
    
    def unregister_websocket(self, task_id: str, connection_id: str):
        """注销WebSocket连接"""
        with self._lock:
            if task_id in self._websocket_connections:
                self._websocket_connections[task_id].discard(connection_id)
                if not self._websocket_connections[task_id]:
                    del self._websocket_connections[task_id]
    
    def update_progress(self, task_id: str, progress: int, message: str = None):
        """更新任务进度"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]['progress'] = progress
                if message:
                    self._tasks[task_id]['message'] = message
    
    def complete_task(self, task_id: str, success: bool = True, error: str = None):
        """完成任务"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]['status'] = 'completed' if success else 'failed'
                self._tasks[task_id]['progress'] = 100 if success else 0
                self._tasks[task_id]['completed_at'] = datetime.now().isoformat()
                if error:
                    self._tasks[task_id]['error'] = error
                if success:
                    self._tasks[task_id]['message'] = '初始化完成'
    
    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_websocket_connections(self, task_id: str) -> Set[str]:
        """获取任务的WebSocket连接"""
        with self._lock:
            return self._websocket_connections.get(task_id, set()).copy()
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """清理已完成的任务"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self._lock:
            tasks_to_remove = []
            for task_id, task_info in self._tasks.items():
                if task_info['status'] in ['completed', 'failed']:
                    completed_at = datetime.fromisoformat(task_info['completed_at'])
                    if completed_at.timestamp() < cutoff_time:
                        tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
                if task_id in self._websocket_connections:
                    del self._websocket_connections[task_id]

# 全局进度管理器实例
progress_manager = ProgressManager()

def create_progress_callback(task_id: str):
    """创建进度回调函数"""
    def callback(progress: int, message: str = None):
        """C++回调函数，接收进度百分比和消息"""
        print(f"C++回调函数，接收进度百分比: {int(progress*100)}%")
        if message:
            progress_manager.update_progress(task_id, int(progress*100), message)
        else:
            progress_manager.update_progress(task_id, progress, f"处理进度: {progress}%")
    
    return callback
