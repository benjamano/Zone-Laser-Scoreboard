# backend/app.py

import os
from flask import Flask
from flask_socketio import SocketIO
from flask_migrate import Migrate

from data.models import db  

from func.DB import context as DBContext
from func.Supervisor import Supervisor

"""

python -m flask --app func.createApp db migrate -m "Initial DB Creation"

python -m flask --app func.createApp db upgrade  

"""

def create_app(supervisor = None):
    if supervisor == "None":
        return
    
    BasePath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    if "\\backend\\" in BasePath:
        BasePath = BasePath.replace("backend\\", "") 
    
    staticPath = os.path.join(BasePath, "frontend\\static")
    templatePath = os.path.join(BasePath, "frontend\\templates")
    databasePath = os.path.join(BasePath, "Scoreboard.db")
    
    if "\\backend\\" in databasePath:
        databasePath = databasePath.replace("backend\\", "") 
    if "\\backend\\" in templatePath:
        templatePath = templatePath.replace("backend\\", "") 
    if "\\backend\\" in staticPath:
        staticPath = staticPath.replace("backend\\", "") 
    
    print(f"Searching for static files here: {staticPath}\nSearching for templates here: {templatePath}")
    print(f"Creating Database here: {databasePath}")
    
    app = Flask(
        __name__,
        template_folder=templatePath,
        static_folder=staticPath,
    )

    app.config['SECRET_KEY'] = 'SJ8SU0D2987G887vf76g87whgd87qwgs87G78GF987EWGF87GF897GH8'
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{databasePath}"
    
    db.init_app(app)
    
    Migrate(app, db)

    socketio = SocketIO(app, cors_allowed_origins="*")

    db_context = DBContext(app, supervisor, db)

    return app, socketio, db_context

try:
    app, socketio, dbContext = create_app()
except Exception as e:
    pass

if __name__ == '__main__':
    pass
