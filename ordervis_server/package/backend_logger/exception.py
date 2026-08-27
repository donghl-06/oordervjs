class LogLevelErrorException(Exception):
    def __init__(self, exception_description="Log level is not supported"):
        super().__init__(self)
        self.__error_msg = exception_description
    
    def __str__(self):
        return self.__error_msg

