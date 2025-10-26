import asyncio
from Utilities.Container import Container
from Utilities.networkUtils import is_app_already_running
from Utilities.checkDependencies import VerifyDependencies
from Web.webApp import WebApp
from Utilities.format import Format
import ctypes
import os

f = Format("Startup")

async def start():
    if is_app_already_running():
        raise RuntimeError("Port in use, app is probably already running. Exiting application.")
    
    VerifyDependencies()

    container = Container()
    
    container.music_api_routes.init()
    container.init_api_routes.init()
    container.supervisor.init() 

    from VRS.VRS import start_vrs_projector_thread
    
    static_web_monitor = os.getenv("STATIC_WEB_MONITOR_INDEX")
    
    if static_web_monitor is not None and static_web_monitor.strip():
        # Start VRS with both windows
        vrs_container = start_vrs_projector_thread(
            container.vrs_projector_factory,
        )
        vrs_instance = vrs_container['vrs']
        static_web_instance = vrs_container['static_web']
        f.message(f"VRS started with static web window on monitor {static_web_monitor}", "success")
    else:
        # Start VRS with only main window (backward compatible)
        vrs_container = start_vrs_projector_thread(container.vrs_projector_factory)
        vrs_instance = vrs_container['vrs']
        static_web_instance = None
        f.message("VRS started with main window only", "warning")

    webApp = WebApp(
        container.app(),
        container.socketio(),
        container.db_context(),
        container.dmx_service(),
        container.music_api(),
        container.email_api(),
        container.feedback_api(),
        container.init_api(),
        container.bpm_fetcher(),
        container.secrets(),
        vrs_instance
    )

    await webApp.start()

if __name__ == "__main__":
    ctypes.windll.kernel32.SetConsoleTitleW("Zone Laser Scoreboard - Ben Mercer")
    start_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(start_loop)
    start_loop.run_until_complete(start())
