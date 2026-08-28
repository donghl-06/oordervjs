#!/usr/bin/env python3
"""
Progress HTTP API 路由
提供进度查询的 HTTP 接口
"""

from fastapi import APIRouter
from ordervis_server.utils.progress_manager import progress_manager

router = APIRouter()

@router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """获取任务进度信息"""
    task_info = progress_manager.get_task_info(task_id)
    
    if not task_info:
        return {
            "code": 1,
            "data": None,
            "message": f"任务 {task_id} 不存在"
        }
    
    return {
        "code": 0,
        "data": task_info,
        "message": "获取进度信息成功"
    }
