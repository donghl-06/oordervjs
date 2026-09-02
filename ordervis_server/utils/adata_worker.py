#!/usr/bin/env python3
"""在独立子进程中拉取 adata 数据，避免阻塞 FastAPI 主进程。"""

import multiprocessing
import os
import tempfile
import threading
import time
from typing import Optional


DEFAULT_FETCH_TIMEOUT_SECONDS = float(os.getenv("ADATA_FETCH_TIMEOUT_SECONDS", "90"))
_fetch_lock = threading.Lock()


def _fetch_dataset_worker(dataset: str, date: str, symbol: str, output_path: str, connection) -> None:
    """子进程入口：拉取、转换并写入临时 CSV。"""
    try:
        from ordervis_server.utils.adata_session import ensure_adata_session_or_raise
        from ordervis_server.utils.adata_converter import (
            get_csord_ad,
            get_cstick_ad,
            get_cstra_ad,
            save_to_csv,
        )

        ensure_adata_session_or_raise()
        fetchers = {
            "cstra": get_cstra_ad,
            "csord": get_csord_ad,
            "cstick": get_cstick_ad,
        }
        fetcher = fetchers.get(dataset)
        if fetcher is None:
            raise ValueError(f"不支持的 adata 数据类型: {dataset}")

        max_attempts = max(1, int(os.getenv("ADATA_FETCH_MAX_ATTEMPTS", "3")))
        retryable_markers = (
            "RETRYABLE",
            "HttpResponseCode:503",
            "Service Unavailable",
            "Connection reset",
            "timed out",
        )
        for attempt in range(1, max_attempts + 1):
            try:
                dataframe = fetcher(date, symbol)
                save_to_csv(dataframe, output_path)
                connection.send({"success": True})
                break
            except BaseException as exc:
                is_retryable = any(marker in str(exc) for marker in retryable_markers)
                if not is_retryable or attempt >= max_attempts:
                    raise
                time.sleep(min(2 ** (attempt - 1), 4))
    except BaseException as exc:
        try:
            connection.send({"success": False, "error": str(exc)})
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        connection.close()


def fetch_dataset_to_csv(
    dataset: str,
    date: str,
    symbol: str,
    target_path: str,
    timeout_seconds: Optional[float] = None,
) -> None:
    """
    在隔离子进程中获取一个数据集，并原子写入 target_path。

    同一后端进程内串行访问 adata，避免认证客户端和连接被并发调用。
    """
    timeout = timeout_seconds or DEFAULT_FETCH_TIMEOUT_SECONDS
    target_dir = os.path.dirname(os.path.abspath(target_path))
    os.makedirs(target_dir, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(
        prefix=f".{dataset}_{symbol}_{date}_",
        suffix=".part.csv",
        dir=target_dir,
    )
    os.close(fd)
    os.unlink(temporary_path)

    process = None
    parent_connection = None
    with _fetch_lock:
        try:
            # Linux 服务端使用 fork 继承已完成初始化的 adata 模块；网络调用在
            # 独立解释器中执行，即使库持有 GIL，也不会拖死 FastAPI 主进程。
            context = multiprocessing.get_context("fork")
            parent_connection, child_connection = context.Pipe(duplex=False)
            process = context.Process(
                target=_fetch_dataset_worker,
                args=(dataset, date, symbol, temporary_path, child_connection),
                daemon=True,
            )
            process.start()
            child_connection.close()

            deadline = time.monotonic() + timeout
            result = None
            while time.monotonic() < deadline:
                if parent_connection.poll(0.2):
                    result = parent_connection.recv()
                    break
                if not process.is_alive():
                    break

            if result is None and parent_connection.poll():
                result = parent_connection.recv()

            if result is None:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=3)
                if process.is_alive():
                    process.kill()
                raise TimeoutError(
                    f"adata 拉取 {dataset} 超过 {timeout:g} 秒，已终止本次任务"
                )

            process.join(timeout=3)
            if not result.get("success"):
                raise RuntimeError(result.get("error") or f"adata 拉取 {dataset} 失败")
            if not os.path.exists(temporary_path):
                raise RuntimeError(f"adata 拉取 {dataset} 完成但未生成数据文件")

            os.replace(temporary_path, target_path)
        finally:
            if process is not None and process.is_alive():
                process.terminate()
                process.join(timeout=1)
                if process.is_alive():
                    process.kill()
            if parent_connection is not None:
                parent_connection.close()
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
