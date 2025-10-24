import threading
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt as CoreQt, QTimer, Signal, Slot
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
    
    vrs_container['ready'].wait(timeout=30)
    return vrs_container['instance']

class VRSProjector(QMainWindow):
    show_idle_signal = Signal()
    play_video_signal = Signal(object)
    show_page_signal = Signal(str)
    switch_view_signal = Signal(int)
    
    def __init__(self, monitor_index=None):
        self.scenes = {
            0: "Web View",
            1: "Video Playback",
            2: "Camera Capture",
            3: "Idle Screen"
        }
        
        if monitor_index is None:
            monitor_index = int(os.getenv("PREFERRED_MONITOR_INDEX", 1))
        super().__init__()
        
        self.show_idle_signal.connect(self._show_idle_slot)
        self.play_video_signal.connect(self._play_video_slot)
        self.show_page_signal.connect(self._show_page_slot)
        self.switch_view_signal.connect(self._switch_view_slot)

        monitor = screeninfo.get_monitors()[monitor_index]
        
        if os.environ["USE_VRS"] == "False":
            self.setWindowState(self.windowState() & ~CoreQt.WindowState.WindowFullScreen | CoreQt.WindowState.WindowNoState)
            self.showMinimized()
            self.setGeometry(
                monitor.x + int(monitor.width / 4),
                monitor.y + int(monitor.height / 4),
                int(monitor.width / 2),
                int(monitor.height / 2)
            )
        else:
            self.showFullScreen()
            # self.setWindowFlags(CoreQt.WindowType.FramelessWindowHint)
            self.setGeometry(monitor.x, monitor.y, monitor.width, monitor.height)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Set background to pure black
        self.setStyleSheet("background-color: rgb(0, 0, 0);")
        self.stacked_widget.setStyleSheet("background-color: rgb(0, 0, 0);")

        # Web view setup (index 0)
        self.web_view = QWebEngineView()
        self.web_view.setPage(NoDialogWebPage(self.web_view))
        self.web_view.load(f"http://{get_local_ip()}:8080/")
        self.stacked_widget.addWidget(self.web_view)

        # Video file setup (index 1)
        self.video_widget = QVideoWidget()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.stacked_widget.addWidget(self.video_widget)

        # Camera capture setup (index 2)
        self.camera_label = QLabel()
        self.camera_label.setAlignment(CoreQt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("background-color: rgb(0, 0, 0);")
        self.camera_label.setScaledContents(True)  # Enable scaling to fill the label
        self.cap = None
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera_frame)
        self.stacked_widget.addWidget(self.camera_label)
        
        # Pre-load default camera at startup to eliminate delay when switching
        self.default_camera_index = int(os.getenv("PREFERRED_SCOREBOARD_CAPTURE_DEVICE_INDEX", 0))
        self._preload_camera()

        # Idle screen setup (index 3)
        self.idle_container = QWidget()
        idle_layout = QVBoxLayout()
        
        title_label = QLabel()
        title_label.setAlignment(CoreQt.AlignmentFlag.AlignCenter)
        title_label.setText("""
        <span style="font-family:'ModeSeven'; font-size:32pt; font-weight:bold;">
        <span style="font-size:50pt;">V</span>ideo 
        <span style="font-size:50pt;">R</span>endering 
        <span style="font-size:50pt;">S</span>ystem
        </span>
        <div style="font-size:20pt; margin-top: 10px; font-family:'ModeSeven';">Maintained By Ben Mercer</div>
        """)
        
        status_label = QLabel("Idle")
        status_label.setAlignment(CoreQt.AlignmentFlag.AlignCenter)
        idle_font = QFont("ModeSeven", 20)
        idle_font.setBold(True)
        status_label.setFont(idle_font)
        
        idle_layout.addWidget(title_label)
        idle_layout.addWidget(status_label)
        self.idle_container.setLayout(idle_layout)
        self.stacked_widget.addWidget(self.idle_container)

        # View indices
        self.VIEW_WEB = 0
        self.VIEW_VIDEO = 1
        self.VIEW_CAMERA = 2
        self.VIEW_IDLE = 3

        self._show_idle_slot()

        self.show()
    
    def _preload_camera(self):
        """Pre-load the default camera to eliminate startup delay when switching to camera view"""
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.default_camera_index)
            if not self.cap.isOpened():
                print(f"Warning: Could not pre-load camera {self.default_camera_index}")
                self.cap = None
            else:
                print(f"Camera {self.default_camera_index} pre-loaded successfully")
    
    # Public methods that can be called from other threads
    def show_idle(self):
        """Thread-safe method to show idle screen"""
        self.show_idle_signal.emit()
    
    def play_video(self, source):
        """Thread-safe method to play video"""
        self.play_video_signal.emit(source)
    
    def show_page(self, url):
        """Thread-safe method to show web page"""
        self.show_page_signal.emit(url)
    
    def switch_view_to_index(self, index: int):
        """Thread-safe method to switch view by index"""
        self.switch_view_signal.emit(index)
    
    # Slot methods that execute in the Qt main thread
    @Slot()
    def _show_idle_slot(self):
        # Stop camera timer if running
        if self.camera_timer.isActive():
            self.camera_timer.stop()
            
        # Keep camera pre-loaded for instant switching (don't release it)
        # Only release if it's not the default camera
        # This maintains the pre-loaded state for fast switching

        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.stop()
            
        # Switch to idle view
        self.stacked_widget.setCurrentIndex(self.VIEW_IDLE)

    @Slot(object)
    def _play_video_slot(self, source):
        # Stop any currently playing video or camera feed
        if self.camera_timer.isActive():
            self.camera_timer.stop()

        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.stop()

        # Handle new source
        if isinstance(source, int):
            # Check if we need to switch to a different camera
            if source != self.default_camera_index:
                # Release current camera and open the requested one
                if self.cap:
                    self.cap.release()
                self.cap = cv2.VideoCapture(source)
                if not self.cap.isOpened():
                    print(f"Cannot open camera {source}")
                    # Try to restore default camera
                    self._preload_camera()
                    return
            else:
                # Use pre-loaded default camera
                if not self.cap or not self.cap.isOpened():
                    self._preload_camera()
                    if not self.cap or not self.cap.isOpened():
                        print(f"Cannot open camera {source}")
                        return

            # Switch to camera view
            self.stacked_widget.setCurrentIndex(self.VIEW_CAMERA)
            # Start timer to update camera frames at ~30 FPS
            self.camera_timer.start(33)

        elif isinstance(source, str):
            # Switch to video view
            self.stacked_widget.setCurrentIndex(self.VIEW_VIDEO)
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

    @Slot(str)
    def _show_page_slot(self, url):
        # Stop camera timer if running
        if self.camera_timer.isActive():
            self.camera_timer.stop()
            
        # Keep camera pre-loaded for instant switching (don't release it)

        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.stop()

        # Switch to web view
        self.stacked_widget.setCurrentIndex(self.VIEW_WEB)
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
        # Scale pixmap to fill the entire label (screen) while maintaining aspect ratio
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.camera_label.size(), 
            CoreQt.AspectRatioMode.KeepAspectRatio,
            CoreQt.TransformationMode.SmoothTransformation
        )
        self.camera_label.setPixmap(scaled_pixmap)
        
    @Slot(int)
    def _switch_view_slot(self, index: int):
        """Slot to switch view (runs in Qt main thread)"""
        # Stop camera timer if switching away from camera
        if self.stacked_widget.currentIndex() == self.VIEW_CAMERA and self.camera_timer.isActive():
            self.camera_timer.stop()
            
        # Stop video if switching away from video
        if self.stacked_widget.currentIndex() == self.VIEW_VIDEO and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.stop()
        
        # Load default content based on view type
        if index == self.VIEW_WEB:
            # Load default web page
            self.web_view.load(f"http://{get_local_ip()}:8080/dynamicRendering/gameResults?mainText=TEST MODE")
            self.stacked_widget.setCurrentIndex(index)
            
        elif index == self.VIEW_VIDEO:
            # Load default video file
            self.stacked_widget.setCurrentIndex(index)
            self.player.setSource("src/VRS/media/Briefing.mp4")
            self.player.mediaStatusChanged.connect(self._on_media_status_changed)
            self.player.play()
            
        elif index == self.VIEW_CAMERA:
            # Use pre-loaded camera for instant switching
            if not self.cap or not self.cap.isOpened():
                # If camera is not ready, try to re-initialize it
                self._preload_camera()
            
            if self.cap and self.cap.isOpened():
                self.stacked_widget.setCurrentIndex(index)
                self.camera_timer.start(33)
            else:
                print(f"Cannot open camera {self.default_camera_index}")
                
        elif index == self.VIEW_IDLE:
            # Just switch to idle view (no content to load)
            self.stacked_widget.setCurrentIndex(index)
        else:
            # Unknown index, just switch
            self.stacked_widget.setCurrentIndex(index)
            
    
    
    def get_current_view(self) -> str:
        return self.scenes[self.stacked_widget.currentIndex()]
    
    def get_views(self) -> dict[int, str]:
        return self.scenes

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
