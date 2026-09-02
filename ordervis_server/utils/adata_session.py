#!/usr/bin/env python3
"""
adata 会话保活：在拉取数据前确保访问令牌有效。

NOTE: aauth.AAuthClient.is_alive 会在访问令牌过期时尝试 refresh；
仅当 refresh 失败或从未登录时，才使用环境变量 aq_username / aq_password 调用 adata.login。
"""

import os
import threading

from ordervis_server.package import backend_logger

_adata_session_lock = threading.Lock()
_logger = backend_logger.Log("adata_session")
_log_level = backend_logger.LogLevel


def ensure_adata_session() -> bool:
    """
    确保 adata 会话有效（必要时通过 refresh 或重新登录恢复）。

    @return bool 会话可用返回 True；缺少凭证或登录失败返回 False
    """
    with _adata_session_lock:
        # adata 导入时会联网更新元数据，必须延迟到隔离工作进程中执行，
        # 否则 FastAPI 会在监听端口之前被阻塞。
        import adata
        from aauth.client import AAuthClient

        try:
            # NOTE: is_alive 会同步磁盘 token，并在 access 过期时尝试 refresh
            if AAuthClient().is_alive:
                return True
        except Exception as e:
            _logger.n_log(f"adata 会话状态检查异常: {e}", _log_level.WARNING)

        username = os.getenv("aq_username")
        password = os.getenv("aq_password")
        if not username or not password:
            _logger.n_log(
                "adata 需要重新登录但未配置 aq_username 或 aq_password",
                _log_level.ERROR,
            )
            return False

        try:
            adata.login(username, password)
            _logger.n_log(f"adata 已重新登录: {username}", _log_level.INFO)
            return True
        except Exception as e:
            _logger.n_log(f"adata 重新登录失败: {e}", _log_level.ERROR)
            return False


def ensure_adata_session_or_raise() -> None:
    """
    与 ensure_adata_session 相同，但在无法恢复会话时抛出 RuntimeError。

    @raises RuntimeError 会话无法恢复时
    """
    if not ensure_adata_session():
        raise RuntimeError(
            "adata 会话无效或缺少凭证（aq_username / aq_password），无法拉取数据"
        )
