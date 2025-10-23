import socket, psutil
import os
from dotenv import load_dotenv
import socket   

load_dotenv("../../.env")

def get_local_ip() -> str:
    try:
        localIp: str = get_ip_by_adapter(os.getenv("PREFERRED_NETWORK_INTERFACE", ""))
        if localIp == "":
            localIp = get_ip_by_socket()
        return localIp
    except Exception as e:
        return get_ip_by_socket()

def get_ip_by_socket() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        localIp: str = s.getsockname()[0]
        s.close()
        return localIp
    except Exception as e:
        raise

def get_ip_by_adapter(adapter_name: str) -> str:
    try:
        addrs = psutil.net_if_addrs()   
        for name, iface_addrs in addrs.items():
            if name.lower() == adapter_name.lower():
                for addr in iface_addrs:
                    if addr.family == socket.AF_INET:
                        return addr.address
        return ""
    except Exception as e:
        raise
    
def is_app_already_running() -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    localIp = s.getsockname()[0]
    s.close()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex((localIp, 8080)) == 0:
            print(f"Port 8080 is already in use on {localIp}")
            return True
    return False