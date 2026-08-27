import platform

def get_split_symbol() -> str:
     os_type = platform.system()
     if os_type.lower() == "linux":
         return '/'
     if os_type.lower() == "windows":
         return '\\' 
