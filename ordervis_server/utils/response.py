from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
from ordervis_server.config.exception import StatusCodeUnregisteredException, ResponseEntityUnsupportException
from ordervis_server.config.response import status_code_map


def response_format(msg: str, response_code: int, data_entity: Any = [], length: int = -1, headers: Dict = {}):
    """格式化响应数据"""
    if length == -1:
        length = len(data_entity) if isinstance(data_entity, (list, dict)) else 1
    if not (isinstance(data_entity, list) or isinstance(data_entity, dict)):
        data_entity = [data_entity]
    response_dict = {
        "msg": msg,
        "data": data_entity,
        "length": length
    }
    return make(response_dict, response_code, **headers)


def make(response_dict: Dict, status_code: int, **headers) -> JSONResponse:
    """创建FastAPI响应"""
    if not isinstance(response_dict, dict):
        raise ResponseEntityUnsupportException
    if status_code not in status_code_map.keys():
        raise StatusCodeUnregisteredException
    
    response = JSONResponse(content=response_dict, status_code=status_code)
    for key, value in headers.items():
        response.headers[key] = value
    return response


def error_response() -> JSONResponse:
    """错误响应"""
    response_body = {
        "msg": "服务器发生内部错误，请联系服务器管理员",
        "data": {},
        "length": 0
    }
    return make(response_body, 500) 