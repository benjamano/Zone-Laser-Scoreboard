import asyncio
from Utilities.Container import Container
from Utilities.networkUtils import is_app_already_running
from Utilities.checkDependencies import VerifyDependencies
from Web.webApp import WebApp
import ctypes

async def start():
    if is_app_already_running():
        raise RuntimeError("Port in use, app is probably already running. Exiting application.")
    
    VerifyDependencies()

    container = Container()
    
    container.music_api_routes.init()
    container.init_api_routes.init()

    from VRS.VRS import start_vrs_projector_thread
    vrs_instance = start_vrs_projector_thread(container.vrs_projector_factory)

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
