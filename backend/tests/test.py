import winrt.windows.media.control as wmc
import asyncio

async def get_media_status():
    sessions = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
    current_session = sessions.get_current_session()

    if current_session:
        info = await current_session.try_get_media_properties_async()
        playback_info = current_session.get_playback_info()

        # Get media playback status
        if playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
            return f"Currently playing: {info.title}"
        elif playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED:
            return "Media is paused"
        elif playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.STOPPED:
            return "Media is stopped"
        else:
            return "No media playing or unknown status"
    else:
        return "No active media session"

# Run the async function and print the result
status = asyncio.run(get_media_status())
print(status)
