import os
from flask import Flask
from flask_socketio import SocketIO
from flask_migrate import Migrate

from data.models import db  

from API.DB import context as DBContext
from API.format import Format

f = Format("Create App")

"""

cd backend

python -m flask --app API.createApp:createApp db migrate -m "Initial DB Creation"

python -m flask --app API.createApp:createApp db migrate 

"""

def createApp():
    BasePath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    BasePath = BasePath.replace("\\backend", "")

    staticPath = os.path.join(BasePath, "frontend", "static")
    templatePath = os.path.join(BasePath, "frontend", "templates")
    databasePath = os.path.join(BasePath, "Scoreboard.db")
    
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
    socketio = SocketIO(app, cors_allowed_origins="*")
    db_context = DBContext(app, db)

    return app, socketio, db_context