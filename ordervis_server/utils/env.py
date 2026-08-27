import platform

def split():
     os_type = platform.system()
     if os_type.lower() == "linux":
         return '/'
     if os_type.lower() == "windows":
         return '\\'    
