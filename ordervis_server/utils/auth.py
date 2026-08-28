#!/usr/bin/env python3
"""
FastAPI第三方认证模块
只验证token有效性，不处理用户登录
"""

from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel
from ordervis_server.package import backend_logger

# JWT Bearer认证
security = HTTPBearer(auto_error=False)

# 日志
logger = backend_logger.Log("auth")
log_level = backend_logger.LogLevel

class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None

def verify_third_party_token(token: str) -> Optional[TokenData]:
    """
    验证第三方认证系统的token
    
    这里需要根据具体的第三方认证系统来修改验证逻辑
    例如：JWT、OAuth2、自定义token等
    """
    try:
        from ordervis_server.config.auth_config import CURRENT_AUTH_CONFIG
        
        # 使用配置文件中的设置
        config = CURRENT_AUTH_CONFIG
        
        # 验证JWT token
        payload = jwt.decode(
            token, 
            config.SECRET_KEY, 
            algorithms=[config.ALGORITHM],
            verify_exp=config.VERIFY_EXPIRATION,
            issuer=config.ISSUER if config.VERIFY_ISSUER else None,
            audience=config.AUDIENCE if config.VERIFY_AUDIENCE else None
        )
        
        # 从token中提取用户信息（使用字段映射）
        user_id = None
        username = None
        role = None
        
        # 查找用户ID
        for field in config.TOKEN_FIELD_MAPPING["user_id"]:
            if field in payload:
                user_id = payload[field]
                break
        
        # 查找用户名
        for field in config.TOKEN_FIELD_MAPPING["username"]:
            if field in payload:
                username = payload[field]
                break
        
        # 查找角色
        for field in config.TOKEN_FIELD_MAPPING["role"]:
            if field in payload:
                role = payload[field]
                break
        
        if not user_id:
            return None
            
        # 使用默认角色如果没有找到
        if not role:
            role = config.DEFAULT_ROLE
            
        return TokenData(
            user_id=str(user_id),
            username=username,
            role=role
        )
        
    except jwt.PyJWTError as e:
        logger.n_log(f"Token验证失败: {e}", log_level.WARNING)
        return None
    except Exception as e:
        logger.n_log(f"Token验证异常: {e}", log_level.ERROR)
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """获取当前用户（从第三方token中）"""
    # 检查是否提供了认证凭据
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    token_data = verify_third_party_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": token_data.user_id,
        "username": token_data.username,
        "role": token_data.role
    }

def require_auth():
    """认证依赖装饰器"""
    return Depends(get_current_user)

def require_role(required_role: str):
    """角色验证装饰器"""
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user
    return role_checker

def verify_token_only(token: str) -> bool:
    """
    仅验证token是否有效，不返回用户信息
    用于简单的token有效性检查
    """
    token_data = verify_third_party_token(token)
    return token_data is not None 