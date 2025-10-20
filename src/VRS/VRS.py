from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt
import screeninfo
import os
from dotenv import load_dotenv
from Utilities.networkUtils import *

load_dotenv()

# Video Rendering System

class VRSProjector():
    def __init__(self):
        app = QApplication()

        self.window = VRSApp(monitor_index=int(os.getenv("PREFERRED_MONITOR_INDEX", 1)), url=f"http://{get_local_ip()}:8080/")
        self.window.show()
        
        app.exec()

class VRSApp(QMainWindow):
    def __init__(self, monitor_index, url):
        super().__init__()

        monitor = screeninfo.get_monitors()[monitor_index]
        self.setGeometry(monitor.x, monitor.y, monitor.width, monitor.height)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        view = QWebEngineView()
        view.load(url)

        label = QLabel("Video Rendering System")
        label.setAlignment(Qt.AlignCenter)

        self.setCentralWidget(view)