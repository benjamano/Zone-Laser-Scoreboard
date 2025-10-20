class AppContext:
    def __init__(self):
        self.app = None
        self.context = None
        self.secrets = None
        self.dir = None

    def setAll(self, app, context, secrets, dir, supervisor, socketio):
        self.app = app
        self.context = context
        self.secrets = secrets
        self.dir = dir
        self.supervisor = supervisor
        self.socketio = socketio