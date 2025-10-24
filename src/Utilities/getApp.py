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
    base_dir = os.path.join(os.path.dirname(__file__), "..", "Data", "migrations", "alembic.ini")
    alembic_cfg = Config(base_dir)
    
    # Set the script location to the migrations directory
    migrations_dir = os.path.join(os.path.dirname(__file__), "..", "Data", "migrations")
    alembic_cfg.set_main_option('script_location', migrations_dir)
    
    command.upgrade(alembic_cfg, 'head')