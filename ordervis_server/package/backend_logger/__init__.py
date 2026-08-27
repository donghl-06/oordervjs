import time
import os
import traceback
from enum import Enum
from .exception import LogLevelErrorException
from functools import wraps
from ._tools import get_split_symbol


class LogLevel(Enum):
    DEBUG=0
    INFO=1
    WARNING=2
    ERROR=3
    CRITICAL=4


class Log:
    def __init__(self, module_name: str, has_date=True):
        self.has_date = has_date
        self.__module_name = module_name
        if has_date:
            self.__file_savename_template = "log/{}_{}.log"
        else:
            self.__file_savename_template = "log/{}.log"
        self.__log_template = "[{} #{}] {}: {}" # 日志等级 时间 模块名 日志信息
        self.__log_buffer = []
        self.__loglevel_map = {
            LogLevel.DEBUG: "DEBUG",
            LogLevel.INFO: "INFO",
            LogLevel.WARNING: "WARNING",
            LogLevel.ERROR: "ERROR",
            LogLevel.CRITICAL: "CRITICAL"
        }
    
    def set_log_path(self, path: str):
        self.__file_savename_template = os.path.join(path, self.__file_savename_template)
    
    def flash_buffer(self):
        if self.has_date:
            save_file = self.__file_savename_template.format(
                "{}".format(time.strftime(r"%Y-%m-%d", time.localtime())),
                self.__module_name
            )
        else:
            save_file = self.__file_savename_template.format(self.__module_name)
        file_path = get_split_symbol().join(self.__file_savename_template.split(get_split_symbol())[:-1])
        if not os.path.exists(file_path):
            try:
                os.mkdir(file_path)
            except PermissionError:
                self.n_log("没有权限读写日志目录或文件", LogLevel.CRITICAL, True)
                return
            except Exception as e:
                self.n_log("出现了设计之外的异常: {}".format(str(e)), LogLevel.CRITICAL, True)
                return
        try:
            with open(save_file, "a") as log_file:
                for single_log in self.__log_buffer:
                    log_file.writelines("{}\n".format(single_log))
            self.__log_buffer = []
        except PermissionError:
            self.n_log("没有权限读写日志目录或文件", LogLevel.CRITICAL, True)
        except Exception as e:
            self.n_log("出现了设计之外的异常: {}".format(traceback.format_exc()), LogLevel.CRITICAL, True)

    def n_log(self, log_msg: str, level, log_only=False):
        if level not in [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]:
            raise LogLevelErrorException
        log_info = self.__log_template.format(
            self.__loglevel_map[level],
            "{}".format(time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime())),
            self.__module_name,
            log_msg
        )
        print(log_info, flush=True)
        if log_only:
            return
        if level in [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]:
            self.__log_buffer.append(log_info)
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.flash_buffer()
        if len(self.__log_buffer) > 0:
            self.flash_buffer()

    def d_log(self, return_func):
        def d_log_body(func):
            @wraps(func)
            def log_func_body(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.n_log("出现了设计之外的异常: {}".format(traceback.format_exc()), LogLevel.CRITICAL)
                self.flash_buffer()
                return return_func()
            return log_func_body
        return d_log_body