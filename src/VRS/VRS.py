import threading
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt as CoreQt, QTimer
from PySide6.QtGui import QFont
import screeninfo
import os
from dotenv import load_dotenv
from Utilities.networkUtils import *
import cv2

os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.multimedia.ffmpeg.debug=false"

load_dotenv()

def start_vrs_projector_thread(vrs_projector_factory, monitor_index=None):
    """Start VRS projector in its own thread and return the instance."""
    vrs_container = {'instance': None, 'ready': threading.Event()}
    
    def run():
        import sys
        app = QApplication(sys.argv)
        vrs_instance = vrs_projector_factory(monitor_index)
        vrs_container['instance'] = vrs_instance
        vrs_container['ready'].set()
        vrs_instance.show()
        app.exec()
    
    threading.Thread(target=run, daemon=True).start()
    
    vrs_container['ready'].wait(timeout=10)
    return vrs_container['instance']

class VRSProjector(QMainWindow):
    def __init__(self, monitor_index=None):
        if monitor_index is None:
            monitor_index = int(os.getenv("PREFERRED_MONITOR_INDEX", 1))
        super().__init__()

        monitor = screeninfo.get_monitors()[monitor_index]
        self.setGeometry(monitor.x, monitor.y, monitor.width, monitor.height)
        self.setWindowFlags(CoreQt.WindowType.FramelessWindowHint)
        self.showFullScreen()

        # Web view setup
        self.web_view = QWebEngineView()
        self.web_view.setPage(NoDialogWebPage(self.web_view))
        self.web_view.load(f"http://{get_local_ip()}:8080/")
        self.setCentralWidget(self.web_view)

        # Video file setup
        self.video_widget = QVideoWidget()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        # Camera capture setup
        self.camera_label = QLabel()
        self.cap = None
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera_frame)
        
        # Initial label setup
        self.label = QLabel(self)
        self.label.setAlignment(CoreQt.AlignmentFlag.AlignCenter)

        self.label.setText("""
        <span style="font-family:'ModeSeven'; font-size:24pt; font-weight:bold;">
        <span style="font-size:40pt;">V</span>ideo 
        <span style="font-size:40pt;">R</span>endering 
        <span style="font-size:40pt;">S</span>ystem
        </span>
        """)
        
        self.idle_label = QLabel("Idle", self)
        self.idle_label.setAlignment(CoreQt.AlignmentFlag.AlignCenter)
        idle_font = QFont("ModeSeven", 20)
        idle_font.setBold(True)
        self.idle_label.setFont(idle_font)

        # Combine both labels in a layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.idle_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # self.play_video(os.getenv("PREFERRED_SCOREBOARD_CAPTURE_DEVICE_INDEX", 0))
        # time.sleep(10)
        # self.show_page(f"http://{get_local_ip()}:8080/")
        # time.sleep(10)
        # self.play_video("src/VRS/media/Briefing.mp4")
        
        # self.play_video(int(os.getenv("PREFERRED_SCOREBOARD_CAPTURE_DEVICE_INDEX", 0)))

        self.show()

    def play_video(self, source):
        # Stop camera timer if running
        if self.camera_timer.isActive():
            self.camera_timer.stop()
            
        if self.cap:
            self.cap.release()
            self.cap = None

        if isinstance(source, int):
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                print(f"Cannot open camera {source}")
                return

            self.camera_label.setAlignment(CoreQt.AlignmentFlag.AlignCenter)
            self.setCentralWidget(self.camera_label)
            # Start timer to update camera frames at ~30 FPS
            self.camera_timer.start(33)

        elif isinstance(source, str):
            self.setCentralWidget(self.video_widget)
            self.player.setSource(source)

            self.player.mediaStatusChanged.connect(self._on_media_status_changed)
            self.player.play()

        else:
            print("Invalid source type for play_video")

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            duration = self.player.duration()
            if duration > 200:
                self.player.setPosition(duration - 100)
            self.player.pause()

    def show_page(self, url):
        # Stop camera timer if running
        if self.camera_timer.isActive():
            self.camera_timer.stop()
            
        if self.cap:
            self.cap.release()
            self.cap = None

        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.stop()

        self.setCentralWidget(self.web_view)
        self.web_view.load(url)

    def update_camera_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        from PySide6.QtGui import QImage, QPixmap
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

class NoDialogWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, line, source):
        print(f"[JS Console] {msg} ({source}:{line})")

    def javaScriptAlert(self, url, msg):
        print(f"[JS Alert] {msg}")

    def javaScriptConfirm(self, url, msg):
        print(f"[JS Confirm] {msg}")
        return False 

    def javaScriptPrompt(self, url, msg, default):
        print(f"[JS Prompt] {msg}")
        return False, ""
