class StatusCodeUnregisteredException(Exception):
    def __init__(self, exception_description="This status code is not registered"):
        super().__init__(self)
        self.__error_msg = exception_description
    
    def __str__(self):
        return self.__error_msg

class ResponseEntityUnsupportException(Exception):
    def __init__(self, exception_description="This response entity must be dict(Type)"):
        super().__init__(self)
        self.__error_msg = exception_description
    
    def __str__(self):
        return self.__error_msg