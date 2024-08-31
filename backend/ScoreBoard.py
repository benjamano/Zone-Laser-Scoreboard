import __init__ as init
import sys

try:
    init.start()
    
    print("|----------------------------------| STARTING WEB APP |----------------------------------------|")
    
    #from waitress import serve
    
    from scapy.all import get_if_list
    
    print(get_if_list())
    
    import webApp as webApp
    import eventlet
    
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8080)), webApp.app)
    
    #webApp.socketio.run(webApp.app, host="0.0.0.0", port=8080)
    #serve(webApp.app, host="0.0.0.0", port=8080)
    #webApp.app.run(debug=False)
    
    
except Exception as e:
    sys.exit(f"An error occured: {e}")