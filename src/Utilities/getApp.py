"""

cd src

python -m flask --app Utilities.getApp db migrate -m "Initial DB Creation"

python -m flask --app Utilities.getApp db upgrade 

python -m flask --app Utilities.getApp db migrate 

"""

from Utilities.createApp import createApp

app = createApp(appOnly=True)

from alembic.config import Config
from alembic import command
import os

def runMigrations():
    base_dir = "Data/migrations/alembic.ini"
    alembic_cfg = Config(base_dir)
    
    command.upgrade(alembic_cfg, 'head')