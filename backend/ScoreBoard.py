import __init__ as init
import sys

try:
    init.start()
    
    print("\n|----------------------------------------------------------------------------------------------------|\n")
    
    #from waitress import serve
    
    from scapy.all import get_if_list, get_if_addr, get_if_hwaddr

    interfaces = get_if_list()

    for iface in interfaces:
            try:
                ip = get_if_addr(iface)
                mac = get_if_hwaddr(iface)
                print(f"Interface: {iface} | IP Address: {ip} | MAC Address: {mac}")
            except Exception as e:
                print(f"Could not retrieve information for interface {iface}: {e}")
                
    import webApp as webApp
    import eventlet
    
    print("""
██╗░░░░░░█████╗░░██████╗███████╗██████╗░░░░░░░████████╗░█████╗░░██████╗░
██║░░░░░██╔══██╗██╔════╝██╔════╝██╔══██╗░░░░░░╚══██╔══╝██╔══██╗██╔════╝░
██║░░░░░███████║╚█████╗░█████╗░░██████╔╝█████╗░░░██║░░░███████║██║░░██╗░
██║░░░░░██╔══██║░╚═══██╗██╔══╝░░██╔══██╗╚════╝░░░██║░░░██╔══██║██║░░╚██╗
███████╗██║░░██║██████╔╝███████╗██║░░██║░░░░░░░░░██║░░░██║░░██║╚██████╔╝
╚══════╝╚═╝░░╚═╝╚═════╝░╚══════╝╚═╝░░╚═╝░░░░░░░░░╚═╝░░░╚═╝░░╚═╝░╚═════╝░

░██████╗░█████╗░░█████╗░██████╗░███████╗██████╗░░█████╗░░█████╗░██████╗░██████╗░
██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗
╚█████╗░██║░░╚═╝██║░░██║██████╔╝█████╗░░██████╦╝██║░░██║███████║██████╔╝██║░░██║
░╚═══██╗██║░░██╗██║░░██║██╔══██╗██╔══╝░░██╔══██╗██║░░██║██╔══██║██╔══██╗██║░░██║
██████╔╝╚█████╔╝╚█████╔╝██║░░██║███████╗██████╦╝╚█████╔╝██║░░██║██║░░██║██████╔╝
╚═════╝░░╚════╝░░╚════╝░╚═╝░░╚═╝╚══════╝╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░

██████╗░██╗░░░██╗  ██████╗░███████╗███╗░░██╗  ███╗░░░███╗███████╗██████╗░░█████╗░███████╗██████╗░
██╔══██╗╚██╗░██╔╝  ██╔══██╗██╔════╝████╗░██║  ████╗░████║██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗
██████╦╝░╚████╔╝░  ██████╦╝█████╗░░██╔██╗██║  ██╔████╔██║█████╗░░██████╔╝██║░░╚═╝█████╗░░██████╔╝
██╔══██╗░░╚██╔╝░░  ██╔══██╗██╔══╝░░██║╚████║  ██║╚██╔╝██║██╔══╝░░██╔══██╗██║░░██╗██╔══╝░░██╔══██╗
██████╦╝░░░██║░░░  ██████╦╝███████╗██║░╚███║  ██║░╚═╝░██║███████╗██║░░██║╚█████╔╝███████╗██║░░██║
╚═════╝░░░░╚═╝░░░  ╚═════╝░╚══════╝╚═╝░░╚══╝  ╚═╝░░░░░╚═╝╚══════╝╚═╝░░╚═╝░╚════╝░╚══════╝╚═╝░░╚═╝""")
    
    print("\n|----------------------------------| STARTING WEB APP |----------------------------------------|\n")
    
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8080)), webApp.app)
    
    #webApp.socketio.run(webApp.app, host="0.0.0.0", port=8080)
    #serve(webApp.app, host="0.0.0.0", port=8080)
    #webApp.app.run(debug=False)
    
    
except Exception as e:
    sys.exit(f"An error occured: {e}")