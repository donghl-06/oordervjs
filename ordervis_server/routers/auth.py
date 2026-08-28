#!/usr/bin/env python3
"""
第三方认证路由模块
只提供token验证功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel
from typing import Optional, List
from ordervis_server.utils.auth import get_current_user, verify_token_only
from ordervis_server.package import backend_logger

router = APIRouter(tags=["认证"])

logger = backend_logger.Log("auth_router")
log_level = backend_logger.LogLevel

class UserInfo(BaseModel):
    user_id: str
    username: Optional[str] = None
    role: Optional[str] = None

class TokenVerifyResponse(BaseModel):
    valid: bool
    user: Optional[UserInfo] = None

# 前端兼容的响应模型
class Role(BaseModel):
    roleName: str
    value: str

class UserDetailInfo(BaseModel):
    userId: str
    username: str
    realName: str
    avatar: str
    desc: str
    token: str
    roles: List[Role]

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    roles: List[Role]
    userId: str
    username: str
    token: str
    realName: str
    desc: str

class ApiResponse(BaseModel):
    code: int
    result: Optional[dict] = None
    message: str
    type: str

# 模拟用户数据（与前端mock保持一致）
FAKE_USERS = {
    "admin": {
        "userId": "1",
        "username": "admin",
        "realName": "ATB Admin",
        "avatar": "https://q1.qlogo.cn/g?b=qq&nk=190848757&s=640",
        "desc": "manager",
        "password": "123456",
        "token": "fakeToken1",
        "roles": [{"roleName": "Super Admin", "value": "super"}]
    },
    "test": {
        "userId": "2",
        "username": "test",
        "realName": "test user",
        "avatar": "https://q1.qlogo.cn/g?b=qq&nk=339449197&s=640",
        "desc": "tester",
        "password": "123456",
        "token": "fakeToken2",
        "roles": [{"roleName": "Tester", "value": "test"}]
    }
}

FAKE_PERM_CODES = {
    "1": ["1000", "3000", "5000"],
    "2": ["2000", "4000", "6000"]
}

@router.post("/login", summary="用户登录")
async def login(login_data: LoginRequest):
    """
    用户登录接口
    
    - **username**: 用户名
    - **password**: 密码
    """
    user = FAKE_USERS.get(login_data.username)
    
    if not user or user["password"] != login_data.password:
        return {
            "code": -1,
            "result": None,
            "message": "Incorrect account or password！",
            "type": "error"
        }
    
    return {
        "code": 0,
        "result": {
            "roles": user["roles"],
            "userId": user["userId"],
            "username": user["username"],
            "token": user["token"],
            "realName": user["realName"],
            "desc": user["desc"]
        },
        "message": "ok",
        "type": "success"
    }

@router.get("/getUserInfo", summary="获取用户信息")
async def get_user_info_api(authorization: Optional[str] = Header(None)):
    """
    获取当前登录用户信息
    
    需要在请求头中携带 Authorization token
    """
    if not authorization:
        return {
            "code": -1,
            "result": None,
            "message": "Invalid token",
            "type": "error"
        }
    
    # 查找匹配的用户
    user = None
    for u in FAKE_USERS.values():
        if u["token"] == authorization:
            user = u
            break
    
    if not user:
        return {
            "code": -1,
            "result": None,
            "message": "The corresponding user information was not obtained!",
            "type": "error"
        }
    
    return {
        "code": 0,
        "result": user,
        "message": "ok",
        "type": "success"
    }

@router.get("/getPermCode", summary="获取权限码")
async def get_perm_code(authorization: Optional[str] = Header(None)):
    """
    获取用户权限码列表
    
    需要在请求头中携带 Authorization token
    """
    if not authorization:
        return {
            "code": -1,
            "result": None,
            "message": "Invalid token",
            "type": "error"
        }
    
    # 查找匹配的用户
    user = None
    for u in FAKE_USERS.values():
        if u["token"] == authorization:
            user = u
            break
    
    if not user:
        return {
            "code": -1,
            "result": None,
            "message": "Invalid token!",
            "type": "error"
        }
    
    code_list = FAKE_PERM_CODES.get(user["userId"], [])
    
    return {
        "code": 0,
        "result": code_list,
        "message": "ok",
        "type": "success"
    }

@router.get("/logout", summary="用户登出")
async def logout(authorization: Optional[str] = Header(None)):
    """
    用户登出接口
    
    需要在请求头中携带 Authorization token
    """
    if not authorization:
        return {
            "code": -1,
            "result": None,
            "message": "Invalid token",
            "type": "error"
        }
    
    # 查找匹配的用户
    user = None
    for u in FAKE_USERS.values():
        if u["token"] == authorization:
            user = u
            break
    
    if not user:
        return {
            "code": -1,
            "result": None,
            "message": "Invalid token!",
            "type": "error"
        }
    
    return {
        "code": 0,
        "result": None,
        "message": "Token has been destroyed",
        "type": "success"
    }

@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """
    获取当前登录用户信息
    
    需要有效的第三方认证令牌
    """
    return UserInfo(
        user_id=current_user["user_id"],
        username=current_user["username"],
        role=current_user["role"]
    )

@router.get("/verify", response_model=TokenVerifyResponse, summary="验证令牌")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    验证第三方认证令牌是否有效
    
    如果令牌有效，返回用户信息
    """
    return TokenVerifyResponse(
        valid=True,
        user=UserInfo(
            user_id=current_user["user_id"],
            username=current_user["username"],
            role=current_user["role"]
        )
    )

@router.post("/verify-only", summary="仅验证令牌有效性")
async def verify_token_only_endpoint(token: str):
    """
    仅验证令牌是否有效，不返回用户信息
    
    - **token**: 要验证的令牌字符串
    """
    is_valid = verify_token_only(token)
    return {"valid": is_valid} 