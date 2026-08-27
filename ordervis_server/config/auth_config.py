#!/usr/bin/env python3
"""
认证配置文件
根据具体的第三方认证系统进行配置
"""

import os
from typing import Optional

# 第三方认证系统配置
class AuthConfig:
    # JWT配置
    SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "your-secret-key")
    ALGORITHM: str = os.getenv("AUTH_ALGORITHM", "HS256")
    
    # Token字段映射（根据第三方系统的token结构配置）
    TOKEN_FIELD_MAPPING = {
        "user_id": ["user_id", "sub", "uid"],  # 用户ID字段名
        "username": ["username", "name", "preferred_username"],  # 用户名字段名
        "role": ["role", "scope", "groups"],  # 角色字段名
    }
    
    # 默认角色
    DEFAULT_ROLE: str = "user"
    
    # Token验证选项
    VERIFY_EXPIRATION: bool = True
    VERIFY_ISSUER: bool = False
    VERIFY_AUDIENCE: bool = False
    
    # 可选的发行者和受众（如果启用验证）
    ISSUER: Optional[str] = None
    AUDIENCE: Optional[str] = None

# 示例：OAuth2配置
class OAuth2Config:
    # OAuth2提供商配置
    PROVIDER_URL: str = os.getenv("OAUTH2_PROVIDER_URL", "")
    CLIENT_ID: str = os.getenv("OAUTH2_CLIENT_ID", "")
    CLIENT_SECRET: str = os.getenv("OAUTH2_CLIENT_SECRET", "")
    
    # 用户信息端点
    USERINFO_ENDPOINT: str = os.getenv("OAUTH2_USERINFO_ENDPOINT", "")

# 示例：自定义认证配置
class CustomAuthConfig:
    # 自定义认证系统配置
    AUTH_SERVER_URL: str = os.getenv("CUSTOM_AUTH_SERVER_URL", "")
    API_KEY: str = os.getenv("CUSTOM_AUTH_API_KEY", "")
    
    # 验证端点
    VERIFY_ENDPOINT: str = os.getenv("CUSTOM_AUTH_VERIFY_ENDPOINT", "")

# 当前使用的认证配置
CURRENT_AUTH_CONFIG = AuthConfig() 