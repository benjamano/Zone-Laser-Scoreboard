from scapy.all import conf, get_if_list

interfaces = get_if_list()

for iface in interfaces:
    print(f"Interface: {iface}")
    if iface in conf.ifaces:
        iface_info = conf.ifaces[iface]
        print(f"  MAC Address: {iface_info.mac}")
        print(f"  IP Address: {iface_info.ip}")
