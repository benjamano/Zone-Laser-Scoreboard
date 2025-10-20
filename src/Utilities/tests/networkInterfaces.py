from scapy.all import conf, get_if_list

interfaces = get_if_list()

for iface in interfaces:
    print(f"Interface: {iface}")
    if iface in conf.ifaces:
        iface_info = conf.ifaces[iface]
        print(f"  MAC Address: {iface_info.mac}")
        print(f"  IP Address: {iface_info.ip}")

import psutil
import socket

for name, addrs in psutil.net_if_addrs().items():
    print(f"\n{name}:")
    for addr in addrs:
        if addr.family == socket.AF_INET:
            print(f"  IPv4: {addr.address}")
        elif addr.family == socket.AF_INET6:
            print(f"  IPv6: {addr.address}")
        elif addr.family == psutil.AF_LINK:
            print(f"  MAC:  {addr.address}")