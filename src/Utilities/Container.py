from dependency_injector import containers, providers
from Web.API.BPM import MediaBPMFetcher
from Web.API.DB import context
from Web.API.DMXControl import dmx
from Web.API.Emails import EmailsAPIController
from Web.API.Feedback.feedback import RequestAndFeedbackAPIController
from Web.API.Initialisation.InitialisationAPIController import InitialisationAPIController
from Web.API.Music.MusicAPIController import MusicAPIController
from Web.API.Supervisor import Supervisor
from Utilities.createApp import createApp
from flask_socketio import SocketIO
from flask import Flask
from dotenv import load_dotenv
from Utilities.format import Format
from VRS.VRS import VRSProjector
import os

class Container(containers.DeclarativeContainer):
    f = Format("App Container")
    f.message(f.colourText("Loading Environment Variables", "Cyan"), type="info")

    config = providers.Configuration()

    load_dotenv(".env")
    secrets = providers.Singleton(lambda: dict(os.environ))

    app_and_context = providers.Singleton(createApp)
    app = providers.Callable(lambda x: x[0], app_and_context)
    socketio = providers.Callable(lambda x: x[1], app_and_context)
    db_context = providers.Callable(lambda x: x[2], app_and_context)

    dmx_service = providers.Singleton(
        dmx,
        db_context,
        socketio,
        app,
        secrets
    )

    email_api = providers.Singleton(
        EmailsAPIController.EmailsAPIController,
        secrets().get("GmailAppPassword"),
        secrets().get("GmailSenderEmail"),
        secrets().get("GmailSenderDisplayName"),
    )

    music_api = providers.Singleton(
        MusicAPIController,
        db_context,
        secrets,
        app,
        dmx_service,
    )
    
    music_api_routes = providers.Resource(
        lambda music_api, app: music_api.registerMusicRoutes(app),
        music_api=music_api,
        app=app,
    )

    feedback_api = providers.Singleton(RequestAndFeedbackAPIController, db_context)
    init_api = providers.Singleton(InitialisationAPIController, db_context)
    
    init_api_routes = providers.Resource(
        lambda init_api, app: init_api.registerInitialisationRoutes(app),
        init_api=init_api,
        app=app,
    )
    
    bpm_fetcher = providers.Singleton(MediaBPMFetcher)
    
    supervisor = providers.Singleton(
        Supervisor,
        dmx=dmx_service,
        context=db_context,
        socket=socketio,
        app=app,
        mApi=music_api,
    )
    
    vrs_projector_factory = providers.Factory(
        VRSProjector,
    )