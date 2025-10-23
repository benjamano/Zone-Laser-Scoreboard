import os
from flask import Flask
from flask_socketio import SocketIO
from flask_migrate import Migrate

from Data.models import db  

from Web.API.DB import context as DBContext
from Utilities.format import Format
from Web.API.Dashboards.DashboardAPIController import registerDashboardRoutes

f = Format("Create App")

def createApp(appOnly = False):
    BasePath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    staticPath = os.path.join(BasePath, "Web", "wwwroot")
    templatePath = os.path.join(BasePath, "Web", "Views")
    databasePath = os.path.join(BasePath, "Data", "Scoreboard.db")
    
    f.message(f"Searching for static files here: {f.colourText(staticPath, 'Red')}")
    f.message(f"Searching for templates here: {f.colourText(templatePath, 'Red')}")
    f.message(f"Creating Database here: {f.colourText(databasePath, 'Red')}")
    
    app = Flask(
        __name__,
        template_folder=templatePath,
        static_folder=staticPath,
    )

    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{databasePath}"
    
    db.init_app(app)
    Migrate(app, db)
    
    if appOnly:
        return app
    
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
    db_context = DBContext(app, db)
    
    f.message(f.colourText("Setting up routes..." ,"Blue"))
    
    registerDashboardRoutes(app, db_context.db)
    
    return app, socketio, db_context