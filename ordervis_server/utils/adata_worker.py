#!/usr/bin/env python3
"""在常驻隔离进程中拉取 adata 数据，避免阻塞 FastAPI 主进程。"""

import atexit
import multiprocessing
import os
import queue
import tempfile
import threading
import time
import uuid
from typing import Optional


DEFAULT_FETCH_TIMEOUT_SECONDS = float(os.getenv("ADATA_FETCH_TIMEOUT_SECONDS", "300"))
_fetch_lock = threading.Lock()
_worker_lock = threading.Lock()
_worker_process = None
_request_queue = None
_response_queue = None


def _worker_loop(request_queue, response_queue) -> None:
    """常驻工作进程：adata 只导入一次，随后串行处理拉取任务。"""
    try:
        from ordervis_server.utils.adata_session import ensure_adata_session_or_raise
        from ordervis_server.utils.adata_converter import (
            get_csord_ad,
            get_cstick_ad,
            get_cstra_ad,
            save_to_csv,
        )

        ensure_adata_session_or_raise()
    except BaseException as exc:
        response_queue.put({"type": "startup", "success": False, "error": str(exc)})
        return

    response_queue.put({"type": "startup", "success": True})
    fetchers = {
        "cstra": get_cstra_ad,
        "csord": get_csord_ad,
        "cstick": get_cstick_ad,
    }
    retryable_markers = (
        "RETRYABLE",
        "HttpResponseCode:503",
        "HttpResponseCode:429",
        "Service Unavailable",
        "Too Many Requests",
        "HTTP 429",
        "Connection reset",
        "timed out",
    )

    while True:
        request = request_queue.get()
        if request is None:
            return

        request_id = request["request_id"]
        dataset = request["dataset"]
        try:
            ensure_adata_session_or_raise()
            fetcher = fetchers.get(dataset)
            if fetcher is None:
                raise ValueError(f"不支持的 adata 数据类型: {dataset}")

            max_attempts = max(1, int(os.getenv("ADATA_FETCH_MAX_ATTEMPTS", "3")))
            for attempt in range(1, max_attempts + 1):
                try:
                    dataframe = fetcher(request["date"], request["symbol"])
                    save_to_csv(dataframe, request["output_path"])
                    break
                except BaseException as exc:
                    is_retryable = any(marker in str(exc) for marker in retryable_markers)
                    if not is_retryable or attempt >= max_attempts:
                        raise
                    time.sleep(min(2 ** (attempt - 1), 4))

            response_queue.put(
                {"type": "result", "request_id": request_id, "success": True}
            )
        except BaseException as exc:
            try:
                response_queue.put(
                    {
                        "type": "result",
                        "request_id": request_id,
                        "success": False,
                        "error": str(exc),
                    }
                )
            except (BrokenPipeError, EOFError, OSError):
                return


def _stop_worker() -> None:
    """停止并清理当前 adata 工作进程。"""
    global _worker_process, _request_queue, _response_queue
    with _worker_lock:
        process = _worker_process
        request_queue = _request_queue
        _worker_process = None
        _request_queue = None
        _response_queue = None

    if process is None:
        return
    if process.is_alive() and request_queue is not None:
        try:
            request_queue.put_nowait(None)
        except (OSError, ValueError):
            pass
        process.join(timeout=2)
    if process.is_alive():
        process.terminate()
        process.join(timeout=3)
    if process.is_alive():
        process.kill()
        process.join(timeout=1)


def _ensure_worker(deadline: float) -> None:
    """按需启动工作进程，并等待 adata 完成一次性导入和会话校验。"""
    global _worker_process, _request_queue, _response_queue
    with _worker_lock:
        if _worker_process is not None and _worker_process.is_alive():
            return

        context = multiprocessing.get_context("spawn")
        _request_queue = context.Queue()
        _response_queue = context.Queue()
        _worker_process = context.Process(
            target=_worker_loop,
            args=(_request_queue, _response_queue),
            daemon=True,
        )
        _worker_process.start()

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        _stop_worker()
        raise TimeoutError("adata 工作进程启动超时")
    try:
        result = _response_queue.get(timeout=remaining)
    except queue.Empty as exc:
        _stop_worker()
        raise TimeoutError("adata 导入或会话初始化超时") from exc

    if result.get("type") != "startup" or not result.get("success"):
        error = result.get("error") or "adata 工作进程启动失败"
        _stop_worker()
        raise RuntimeError(error)


def fetch_dataset_to_csv(
    dataset: str,
    date: str,
    symbol: str,
    target_path: str,
    timeout_seconds: Optional[float] = None,
) -> None:
    """
    通过常驻隔离进程获取一个数据集，并原子写入 target_path。

    第一次调用会等待工作进程完成 adata 导入；后续数据集复用同一进程和会话。
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

    with _fetch_lock:
        try:
            deadline = time.monotonic() + timeout
            _ensure_worker(deadline)
            request_id = uuid.uuid4().hex
            _request_queue.put(
                {
                    "request_id": request_id,
                    "dataset": dataset,
                    "date": date,
                    "symbol": symbol,
                    "output_path": temporary_path,
                }
            )

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise queue.Empty
            result = _response_queue.get(timeout=remaining)
            if result.get("type") != "result" or result.get("request_id") != request_id:
                raise RuntimeError("adata 工作进程返回了无法识别的响应")
            if not result.get("success"):
                raise RuntimeError(result.get("error") or f"adata 拉取 {dataset} 失败")
            if not os.path.exists(temporary_path):
                raise RuntimeError(f"adata 拉取 {dataset} 完成但未生成数据文件")

            os.replace(temporary_path, target_path)
        except queue.Empty as exc:
            _stop_worker()
            raise TimeoutError(
                f"adata 拉取 {dataset} 超过 {timeout:g} 秒，已终止工作进程"
            ) from exc
        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)


atexit.register(_stop_worker)
