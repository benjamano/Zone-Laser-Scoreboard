"""

cd backend

python -m flask --app API.getApp db migrate -m "Initial DB Creation"

python -m flask --app API.getApp db upgrade 

python -m flask --app API.getApp db migrate 

"""

from API.createApp import createApp

app = createApp(appOnly=True)