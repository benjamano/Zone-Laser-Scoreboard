"""

cd backend

python -m flask --app API.getApp db migrate -m "Initial DB Creation"

python -m flask --app API.getApp db upgrade 

python -m flask --app API.getApp db migrate 

"""

from API.createApp import createApp

app = createApp(appOnly=True)

from alembic.config import Config
from alembic import command
import os

def runMigrations():
    return

    # base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'migrations'))
    # alembic_cfg = Config(os.path.join(base_dir, 'alembic.ini'))
    #
    # command.upgrade(alembic_cfg, 'head')