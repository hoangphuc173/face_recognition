"""
Face Recognition GUI Application
Giao diện đẹp với PyQt5 - Quét liên tục + Quản lý Database

Cài đặt:
    pip install PyQt5 opencv-python requests Pillow

Chạy:
    python samples/clients/desktop/gui_app.py
"""

import sys
import cv2
import requests
import time
import os
import uuid
import re
import base64
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QLineEdit,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QGridLayout,
    QSplitter,
    QStatusBar,
    QDialog,
    QFormLayout,
    QTextEdit,
    QSpinBox,
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont

# ============ CẤU HÌNH ============
# API Configuration
USE_LOCAL_API = False  # Set False to use AWS API Gateway
LOCAL_API_URL = "https://ayism4ui59.execute-api.ap-southeast-1.amazonaws.com/prod"  # Backend is running on port 5555
AWS_API_URL = "https://s86huzh4s7.execute-api.ap-southeast-1.amazonaws.com/dev"
API_URL = LOCAL_API_URL if USE_LOCAL_API else AWS_API_URL

# Select API URL based on configuration
API_URL = LOCAL_API_URL if USE_LOCAL_API else AWS_API_URL

CAMERA_ID = 0


# ============ VIDEO THREAD ============
class VideoThread(QThread):
    """Thread xử lý video để không block UI"""

    change_pixmap_signal = pyqtSignal(QImage)
    faces_detected_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.cap = None
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.current_frame = None
        self.faces_count = 0
        self.identify_name = None
        self.identify_confidence = None

    def run(self):
        """Main loop của video thread"""
        self.cap = cv2.VideoCapture(CAMERA_ID)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                self.current_frame = frame.copy()

                # Detect faces
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )

                self.faces_count = len(faces)
                self.faces_detected_signal.emit(len(faces))

                # Draw rectangles and labels
                for x, y, w, h in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Draw identify info if available
                    if self.identify_name and self.identify_confidence:
                        label = f"{self.identify_name} ({self.identify_confidence:.1f}%)"
                        
                        # Draw background for text
                        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                        cv2.rectangle(frame, (x, y - 30), (x + text_w + 10, y), (0, 255, 0), -1)
                        
                        # Draw text
                        cv2.putText(frame, label, (x + 5, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

                # Convert to Qt format
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(
                    rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888
                )
                self.change_pixmap_signal.emit(qt_image)

            time.sleep(0.03)  # ~30 FPS

        if self.cap:
            self.cap.release()

    def stop(self):
        """Stop thread"""
        self._run_flag = False
        self.wait()

    def get_current_frame(self):
        """Lấy frame hiện tại để identify"""
        return self.current_frame
    
    def set_identify_result(self, name, confidence):
        """Set kết quả identify để hiển thị lên frame"""
        self.identify_name = name
        self.identify_confidence = confidence
    
    def clear_identify_result(self):
        """Xóa kết quả identify"""
        self.identify_name = None
        self.identify_confidence = None


# [REMOVED OLD LOGIN CODE - SEE LINE 619 FOR ACTUAL CLASS]
        self.setFixedSize(500, 450)

        # Apply dark theme
        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
            }
            QLabel#titleLabel {
                color: #89b4fa;
                font-size: 24px;
                font-weight: bold;
            }
            QLabel#subtitleLabel {
                color: #6c7086;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #313244;
                border: 2px solid #45475a;
                border-radius: 5px;
                padding: 10px;
                color: #cdd6f4;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:pressed {
                background-color: #74c7ec;
            }
            QPushButton#cancelBtn {
                background-color: #f38ba8;
            }
            QPushButton#cancelBtn:hover {
                background-color: #f5c2e7;
            }
        """
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title_label = QLabel("🔐 Face Recognition")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Please login to continue")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(20)

        # Username
        username_label = QLabel("👤 Username:")
        layout.addWidget(username_label)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your username")
        self.username_edit.setText("admin")  # Default for testing
        layout.addWidget(self.username_edit)

        layout.addSpacing(10)

        # Password
        password_label = QLabel("🔒 Password:")
        layout.addWidget(password_label)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setText("admin123")  # Default for testing
        self.password_edit.returnPressed.connect(self.login)  # Enter to login
        layout.addWidget(self.password_edit)

        layout.addSpacing(20)

        # Login button
        login_btn = QPushButton("🔓 Login")
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)

        # Register button
        register_btn = QPushButton("✨ Create New Account")
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
            }
            QPushButton:hover {
                background-color: #b4e3a5;
            }
        """)
        register_btn.clicked.connect(self.show_register)
        layout.addWidget(register_btn)

        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        layout.addSpacing(10)

        # API mode info
        api_info = QLabel(f"🌐 API: {API_URL}")
        api_info.setAlignment(Qt.AlignCenter)
        api_info.setStyleSheet("color: #6c7086; font-size: 10px;")
        layout.addWidget(api_info)

    def login(self):
        """Xử lý đăng nhập"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            QMessageBox.warning(
                self,
                "Warning",
                "⚠️ Please enter both username and password!",
            )
            return

        # BYPASS MODE: Accept any login for development
        # Remove this in production
        if True:  # Set to False to enable real authentication
            self.auth_token = "dev_token_bypass"
            QMessageBox.information(
                self,
                "Success",
                f"✅ Login successful (Dev Mode)!\n\nWelcome, {username}!\n\n"
                f"Note: Authentication is bypassed for development.\n"
                f"Use: admin / admin123 for real auth when enabled.",
            )
            self.accept()
            return

        try:
            # Call auth API with form data (OAuth2 format)
            response = requests.post(
                f"{API_URL}/auth/token",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                self.auth_token = result.get("access_token")

                if self.auth_token:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"✅ Login successful!\n\nWelcome, {username}!",
                    )
                    self.accept()  # Close dialog with success
                else:
                    QMessageBox.critical(
                        self,
                        "Error",
                        "❌ Login failed: No token received",
                    )
            elif response.status_code == 401:
                QMessageBox.warning(
                    self,
                    "Authentication Failed",
                    "❌ Invalid username or password!\n\nPlease try again.\n\nDefault credentials:\nUsername: admin\nPassword: admin123",
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"❌ API Error: {response.status_code}\n\n{response.text}",
                )

        except requests.exceptions.ConnectionError:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"❌ Cannot connect to API server!\n\n"
                f"API URL: {API_URL}\n\n"
                f"Please check:\n"
                f"1. API server is running\n"
                f"2. Network connection\n"
                f"3. API URL is correct",
            )
        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self,
                "Timeout Error",
                "❌ Request timeout!\n\nThe server is not responding.",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"❌ An error occurred:\n\n{str(e)}",
            )

    def show_register(self):
        """Hiển thị dialog đăng ký"""
        register_dialog = RegisterDialog(self)
        if register_dialog.exec_() == QDialog.Accepted:
            # After successful registration, show message
            QMessageBox.information(
                self,
                "Registration Complete",
                "✅ Account created successfully!\n\nPlease login with your new credentials.",
            )


# ============ REGISTER DIALOG ============
class RegisterDialog(QDialog):
    """Dialog đăng ký tài khoản mới"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """Khởi tạo giao diện đăng ký"""
        self.setWindowTitle("Face Recognition - Register")
        self.setModal(True)
        self.setFixedSize(500, 550)

        # Apply dark theme
        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
            }
            QLabel#titleLabel {
                color: #89b4fa;
                font-size: 24px;
                font-weight: bold;
            }
            QLabel#subtitleLabel {
                color: #6c7086;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #313244;
                border: 2px solid #45475a;
                border-radius: 5px;
                padding: 10px;
                color: #cdd6f4;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b4e3a5;
            }
            QPushButton:pressed {
                background-color: #94d2a3;
            }
            QPushButton#cancelBtn {
                background-color: #f38ba8;
            }
            QPushButton#cancelBtn:hover {
                background-color: #f5c2e7;
            }
        """
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title_label = QLabel("✨ Create New Account")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Register as new user")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(20)

        # Username
        username_label = QLabel("👤 Username:")
        layout.addWidget(username_label)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your username")
        layout.addWidget(self.username_edit)

        layout.addSpacing(10)

        # Full Name
        fullname_label = QLabel("📝 Full Name:")
        layout.addWidget(fullname_label)

        self.fullname_edit = QLineEdit()
        self.fullname_edit.setPlaceholderText("Enter your full name")
        layout.addWidget(self.fullname_edit)

        layout.addSpacing(10)

        # Email
        email_label = QLabel("📧 Email:")
        layout.addWidget(email_label)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter your email")
        layout.addWidget(self.email_edit)

        layout.addSpacing(10)

        # Password
        password_label = QLabel("🔒 Password:")
        layout.addWidget(password_label)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit)

        layout.addSpacing(10)

        # Confirm Password
        confirm_label = QLabel("🔒 Confirm Password:")
        layout.addWidget(confirm_label)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setPlaceholderText("Confirm your password")
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit.returnPressed.connect(self.register)
        layout.addWidget(self.confirm_edit)

        layout.addSpacing(20)

        # Register button
        register_btn = QPushButton("✅ Register")
        register_btn.clicked.connect(self.register)
        layout.addWidget(register_btn)

        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        layout.addSpacing(10)

        # Info
        info_label = QLabel("ℹ️ New accounts are created with 'user' role")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #6c7086; font-size: 10px;")
        layout.addWidget(info_label)

    def register(self):
        """Xử lý đăng ký"""
        username = self.username_edit.text().strip()
        fullname = self.fullname_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text().strip()
        confirm = self.confirm_edit.text().strip()

        # Validation
        if not username or not password or not fullname or not email:
            QMessageBox.warning(
                self,
                "Warning",
                "⚠️ Please fill in all fields!",
            )
            return

        if len(username) < 3:
            QMessageBox.warning(
                self,
                "Warning",
                "⚠️ Username must be at least 3 characters!",
            )
            return

        if len(password) < 6:
            QMessageBox.warning(
                self,
                "Warning",
                "⚠️ Password must be at least 6 characters!",
            )
            return

        if password != confirm:
            QMessageBox.warning(
                self,
                "Warning",
                "⚠️ Passwords do not match!",
            )
            return

        try:
            # Call register API
            response = requests.post(
                f"{API_URL}/auth/register",
                json={
                    "username": username,
                    "full_name": fullname,
                    "email": email,
                    "password": password,
                },
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                QMessageBox.information(
                    self,
                    "Success",
                    f"✅ Registration successful!\n\n"
                    f"Username: {username}\n"
                    f"Role: user\n\n"
                    f"You can now login with your credentials.",
                )
                self.accept()
            elif response.status_code == 400:
                QMessageBox.warning(
                    self,
                    "Registration Failed",
                    f"❌ {response.json().get('detail', 'Username already exists or invalid data')}",
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"❌ API Error: {response.status_code}\n\n{response.text}",
                )

        except requests.exceptions.ConnectionError:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"❌ Cannot connect to API server!\n\n"
                f"API URL: {API_URL}",
            )
        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self,
                "Timeout Error",
                "❌ Request timeout!",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"❌ An error occurred:\n\n{str(e)}",
            )


# ============ MAIN WINDOW ============
class FaceRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video_thread = None
        self.auto_identify_timer = None
        self.is_auto_identify = False
        self.identify_count = 0
        self.fps_counter = 0
        self.fps = 0
        self.is_recording = False
        self.video_writer = None
        self.video_frames = []

        self.initUI()
        self.start_fps_counter()
        self.start_auto_refresh_database()

    def initUI(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("🎥 Face Recognition - Full Management System")
        self.setGeometry(100, 100, 1400, 800)

        # Set theme
        self.set_modern_theme()

        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main layout
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Left panel - Video + Controls
        left_panel = self.create_video_panel()

        # Right panel - Management
        right_panel = self.create_management_panel()

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 700])

        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def set_modern_theme(self):
        """Set modern dark theme"""
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e2e;
            }
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                background-color: #313244;
                border: 2px solid #45475a;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #89b4fa;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:pressed {
                background-color: #74c7ec;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            QPushButton#startBtn {
                background-color: #a6e3a1;
                color: #1e1e2e;
            }
            QPushButton#stopBtn {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
            QPushButton#identifyBtn {
                background-color: #f9e2af;
                color: #1e1e2e;
            }
            QPushButton#autoBtn {
                background-color: #cba6f7;
                color: #1e1e2e;
            }
            QLabel {
                background-color: transparent;
            }
            QLabel#videoLabel {
                background-color: #000000;
                border: 2px solid #45475a;
                border-radius: 8px;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #313244;
                border: 2px solid #45475a;
                border-radius: 5px;
                padding: 8px;
                color: #cdd6f4;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #89b4fa;
            }
            QTableWidget {
                background-color: #313244;
                alternate-background-color: #45475a;
                border: 2px solid #45475a;
                border-radius: 8px;
                gridline-color: #45475a;
            }
            QTableWidget::item {
                padding: 8px;
                color: #cdd6f4;
            }
            QTableWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QHeaderView::section {
                background-color: #45475a;
                color: #89b4fa;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 2px solid #45475a;
                border-radius: 8px;
                background-color: #313244;
            }
            QTabBar::tab {
                background-color: #45475a;
                color: #cdd6f4;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
            }
            QStatusBar {
                background-color: #313244;
                color: #cdd6f4;
                border-top: 2px solid #45475a;
            }
            QTextEdit {
                background-color: #313244;
                border: 2px solid #45475a;
                border-radius: 5px;
                padding: 8px;
                color: #cdd6f4;
            }
        """
        )

    def create_video_panel(self):
        """Tạo panel video + controls"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Video display
        video_group = QGroupBox("📹 Camera Feed")
        video_layout = QVBoxLayout()

        self.video_label = QLabel()
        self.video_label.setObjectName("videoLabel")
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("Camera Stopped\nClick 'Start Camera' to begin")
        self.video_label.setStyleSheet("color: #6c7086; font-size: 16px;")

        video_layout.addWidget(self.video_label)
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)

        # Controls
        controls_group = QGroupBox("🎮 Controls")
        controls_layout = QGridLayout()

        self.start_btn = QPushButton("▶️ Start Camera")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_camera)

        self.stop_btn = QPushButton("⏹️ Stop Camera")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self.stop_camera)
        self.stop_btn.setEnabled(False)

        self.identify_btn = QPushButton("🔍 Identify Now")
        self.identify_btn.setObjectName("identifyBtn")
        self.identify_btn.clicked.connect(self.identify_face)
        self.identify_btn.setEnabled(False)

        self.auto_btn = QPushButton("🔄 Auto: OFF")
        self.auto_btn.setObjectName("autoBtn")
        self.auto_btn.clicked.connect(self.toggle_auto_identify)
        self.auto_btn.setEnabled(False)

        self.record_btn = QPushButton("⏺️ Record: OFF")
        self.record_btn.setStyleSheet(
            "background-color: #f38ba8; color: #1e1e2e; font-weight: bold;"
        )
        self.record_btn.clicked.connect(self.toggle_recording)
        self.record_btn.setEnabled(False)

        controls_layout.addWidget(self.start_btn, 0, 0)
        controls_layout.addWidget(self.stop_btn, 0, 1)
        controls_layout.addWidget(self.identify_btn, 1, 0)
        controls_layout.addWidget(self.auto_btn, 1, 1)
        controls_layout.addWidget(self.record_btn, 2, 0, 1, 2)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Stats
        stats_group = QGroupBox("📊 Statistics")
        stats_layout = QGridLayout()

        self.faces_label = QLabel("Faces: 0")
        self.faces_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #a6e3a1;"
        )

        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #89b4fa;"
        )

        self.identify_count_label = QLabel("Identifications: 0")
        self.identify_count_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #f9e2af;"
        )

        self.result_label = QLabel("Last Result: -")
        self.result_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #cba6f7;"
        )
        self.result_label.setWordWrap(True)

        stats_layout.addWidget(self.faces_label, 0, 0)
        stats_layout.addWidget(self.fps_label, 0, 1)
        stats_layout.addWidget(self.identify_count_label, 1, 0)
        stats_layout.addWidget(self.result_label, 1, 1)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        return panel

    def create_management_panel(self):
        """Tạo panel quản lý database"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Title
        title = QLabel("🗄️ Database Management")
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #89b4fa; padding: 10px;"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # API Mode indicator
        api_mode_label = QLabel(f"🌐 API: {'LOCAL' if USE_LOCAL_API else 'AWS Cloud'}")
        api_mode_label.setStyleSheet(
            f"color: {'#a6e3a1' if USE_LOCAL_API else '#89b4fa'}; font-weight: bold; padding: 5px;"
        )
        api_mode_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(api_mode_label)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: People List
        people_tab = self.create_people_tab()
        self.tabs.addTab(people_tab, "👥 People")

        # Tab 2: Enroll
        enroll_tab = self.create_enroll_tab()
        self.tabs.addTab(enroll_tab, "➕ Enroll")

        # Tab 3: Stats
        stats_tab = self.create_stats_tab()
        self.tabs.addTab(stats_tab, "📊 Stats")

        # Tab 4: Advanced
        advanced_tab = self.create_advanced_tab()
        self.tabs.addTab(advanced_tab, "⚙️ Advanced")

        layout.addWidget(self.tabs)

        return panel

    def create_people_tab(self):
        """Tab danh sách người"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Refresh button and auto-refresh indicator
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh List")
        refresh_btn.clicked.connect(self.load_people_list)
        refresh_layout.addWidget(refresh_btn)

        self.auto_refresh_label = QLabel("🔄 Auto-refresh: ON")
        self.auto_refresh_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        refresh_layout.addWidget(self.auto_refresh_label)
        refresh_layout.addStretch()

        layout.addLayout(refresh_layout)

        # Table
        self.people_table = QTableWidget()
        self.people_table.setColumnCount(5)
        self.people_table.setHorizontalHeaderLabels(
            ["Name", "Folder", "Gender", "Birth Year", "Actions"]
        )
        self.people_table.setAlternatingRowColors(True)
        self.people_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.people_table)

        return tab

    def create_enroll_tab(self):
        """Tab đăng ký mới"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Enroll method selection
        method_group = QGroupBox("📸 Enroll Method")
        method_layout = QHBoxLayout()

        self.enroll_from_file_btn = QPushButton("📁 From File")
        self.enroll_from_file_btn.setStyleSheet(
            "background-color: #89b4fa; padding: 12px;"
        )
        self.enroll_from_file_btn.clicked.connect(self.show_file_enroll_form)

        self.enroll_from_camera_btn = QPushButton("📷 From Camera")
        self.enroll_from_camera_btn.setStyleSheet(
            "background-color: #a6e3a1; padding: 12px;"
        )
        self.enroll_from_camera_btn.clicked.connect(self.show_camera_enroll_form)

        method_layout.addWidget(self.enroll_from_file_btn)
        method_layout.addWidget(self.enroll_from_camera_btn)
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)

        # File enroll form
        self.file_enroll_group = QGroupBox("📝 Enroll From File")
        form_layout = QFormLayout()

        # Image file
        image_layout = QHBoxLayout()
        self.image_path_edit = QLineEdit()
        self.image_path_edit.setPlaceholderText("Select image file...")
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self.browse_image)
        image_layout.addWidget(self.image_path_edit)
        image_layout.addWidget(browse_btn)
        form_layout.addRow("📷 Image:", image_layout)

        # User name
        self.enroll_name_edit = QLineEdit()
        self.enroll_name_edit.setPlaceholderText("Nguyễn Văn A")
        form_layout.addRow("👤 Full Name:", self.enroll_name_edit)

        # Gender
        self.enroll_gender_combo = QComboBox()
        self.enroll_gender_combo.addItems(["", "Nam", "Nữ"])
        form_layout.addRow("⚧ Gender:", self.enroll_gender_combo)

        # Birth year
        self.enroll_birth_spin = QSpinBox()
        self.enroll_birth_spin.setRange(1900, 2024)
        self.enroll_birth_spin.setValue(1990)
        form_layout.addRow("🎂 Birth Year:", self.enroll_birth_spin)

        # Hometown
        self.enroll_hometown_edit = QLineEdit()
        self.enroll_hometown_edit.setPlaceholderText("Hà Nội")
        form_layout.addRow("🏠 Hometown:", self.enroll_hometown_edit)

        # Residence
        self.enroll_residence_edit = QLineEdit()
        self.enroll_residence_edit.setPlaceholderText("TP. Hồ Chí Minh")
        form_layout.addRow("📍 Residence:", self.enroll_residence_edit)

        self.file_enroll_group.setLayout(form_layout)
        layout.addWidget(self.file_enroll_group)

        # Submit button for file
        self.file_submit_btn = QPushButton("➕ Register New Person")
        self.file_submit_btn.setStyleSheet(
            "background-color: #a6e3a1; padding: 15px; font-size: 14px;"
        )
        self.file_submit_btn.clicked.connect(self.enroll_person)
        layout.addWidget(self.file_submit_btn)

        # Camera enroll form (initially hidden)
        self.camera_enroll_group = QGroupBox("📷 Enroll From Camera")
        camera_layout = QVBoxLayout()

        # Preview label
        self.capture_label = QLabel()
        self.capture_label.setObjectName("videoLabel")
        self.capture_label.setMinimumSize(320, 240)
        self.capture_label.setMaximumSize(320, 240)
        self.capture_label.setAlignment(Qt.AlignCenter)
        self.capture_label.setText("Click 'Capture' to take photo")
        self.capture_label.setStyleSheet("color: #6c7086; font-size: 14px;")
        camera_layout.addWidget(self.capture_label, alignment=Qt.AlignCenter)

        # Capture button
        capture_btn = QPushButton("📸 Capture Face from Camera")
        capture_btn.setStyleSheet(
            "background-color: #f9e2af; color: #1e1e2e; padding: 12px; font-weight: bold;"
        )
        capture_btn.clicked.connect(self.capture_face_from_camera)
        camera_layout.addWidget(capture_btn)

        # Form for camera enroll
        camera_form = QFormLayout()

        self.camera_name_edit = QLineEdit()
        self.camera_name_edit.setPlaceholderText("Nguyễn Văn A")
        camera_form.addRow("👤 Full Name:", self.camera_name_edit)

        self.camera_gender_combo = QComboBox()
        self.camera_gender_combo.addItems(["", "Nam", "Nữ"])
        camera_form.addRow("⚧ Gender:", self.camera_gender_combo)

        self.camera_birth_spin = QSpinBox()
        self.camera_birth_spin.setRange(1900, 2024)
        self.camera_birth_spin.setValue(1990)
        camera_form.addRow("🎂 Birth Year:", self.camera_birth_spin)

        self.camera_hometown_edit = QLineEdit()
        self.camera_hometown_edit.setPlaceholderText("Hà Nội")
        camera_form.addRow("🏠 Hometown:", self.camera_hometown_edit)

        self.camera_residence_edit = QLineEdit()
        self.camera_residence_edit.setPlaceholderText("TP. Hồ Chí Minh")
        camera_form.addRow("📍 Residence:", self.camera_residence_edit)

        camera_layout.addLayout(camera_form)

        self.camera_enroll_group.setLayout(camera_layout)
        self.camera_enroll_group.setVisible(False)
        layout.addWidget(self.camera_enroll_group)

        # Submit button for camera
        self.camera_submit_btn = QPushButton("➕ Register from Captured Photo")
        self.camera_submit_btn.setStyleSheet(
            "background-color: #a6e3a1; padding: 15px; font-size: 14px;"
        )
        self.camera_submit_btn.clicked.connect(self.enroll_from_camera)
        self.camera_submit_btn.setVisible(False)
        layout.addWidget(self.camera_submit_btn)

        layout.addStretch()

        # Store captured frame
        self.captured_frame = None

        return tab

    def create_stats_tab(self):
        """Tab thống kê"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Stats")
        refresh_btn.clicked.connect(self.load_stats)
        layout.addWidget(refresh_btn)

        # Stats display
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setPlaceholderText("Click 'Refresh Stats' to load data...")
        layout.addWidget(self.stats_text)

        return tab

    def create_advanced_tab(self):
        """Tab advanced features"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Video enroll group
        video_enroll_group = QGroupBox("🎥 Enroll from Video")
        video_layout = QVBoxLayout()

        video_info = QLabel(
            "Upload video file (.mp4, .avi) to extract all frames for enrollment"
        )
        video_info.setWordWrap(True)
        video_info.setStyleSheet("color: #89b4fa; padding: 10px;")
        video_layout.addWidget(video_info)

        video_select_layout = QHBoxLayout()
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("Select video file...")
        video_browse_btn = QPushButton("📁 Browse Video")
        video_browse_btn.clicked.connect(self.browse_video)
        video_select_layout.addWidget(self.video_path_edit)
        video_select_layout.addWidget(video_browse_btn)
        video_layout.addLayout(video_select_layout)

        video_enroll_btn = QPushButton("🎥 Extract & Enroll from Video")
        video_enroll_btn.setStyleSheet("background-color: #cba6f7; padding: 12px;")
        video_enroll_btn.clicked.connect(self.enroll_from_video)
        video_layout.addWidget(video_enroll_btn)

        video_enroll_group.setLayout(video_layout)
        layout.addWidget(video_enroll_group)

        # Video recognition group
        video_recog_group = QGroupBox("🔍 Recognize from Video")
        recog_layout = QVBoxLayout()

        recog_info = QLabel("Process video file and identify all faces")
        recog_info.setStyleSheet("color: #89b4fa; padding: 10px;")
        recog_layout.addWidget(recog_info)

        recog_select_layout = QHBoxLayout()
        self.recog_video_path_edit = QLineEdit()
        self.recog_video_path_edit.setPlaceholderText("Select video file...")
        recog_browse_btn = QPushButton("📁 Browse Video")
        recog_browse_btn.clicked.connect(self.browse_recog_video)
        recog_select_layout.addWidget(self.recog_video_path_edit)
        recog_select_layout.addWidget(recog_browse_btn)
        recog_layout.addLayout(recog_select_layout)

        recog_btn = QPushButton("🔍 Process & Identify Video")
        recog_btn.setStyleSheet(
            "background-color: #f9e2af; color: #1e1e2e; padding: 12px;"
        )
        recog_btn.clicked.connect(self.recognize_from_video)
        recog_layout.addWidget(recog_btn)

        video_recog_group.setLayout(recog_layout)
        layout.addWidget(video_recog_group)

        # Organization group
        org_group = QGroupBox("📁 File Organization")
        org_layout = QVBoxLayout()

        org_info = QLabel("Organize recognized photos by person")
        org_info.setStyleSheet("color: #89b4fa; padding: 10px;")
        org_layout.addWidget(org_info)

        org_btn = QPushButton("📊 Generate Organization Report")
        org_btn.setStyleSheet("background-color: #74c7ec; padding: 12px;")
        org_btn.clicked.connect(self.generate_organization_report)
        org_layout.addWidget(org_btn)

        org_group.setLayout(org_layout)
        layout.addWidget(org_group)

        # Results
        self.advanced_results = QTextEdit()
        self.advanced_results.setReadOnly(True)
        self.advanced_results.setPlaceholderText("Results will appear here...")
        layout.addWidget(self.advanced_results)

        return tab

    def _get_auth_headers(self):
        """No authentication required - return empty headers"""
        return {}

    # ============ VIDEO FUNCTIONS ============

    def start_camera(self):
        """Bắt đầu camera"""
        if self.video_thread is None or not self.video_thread.isRunning():
            self.video_thread = VideoThread()
            self.video_thread.change_pixmap_signal.connect(self.update_image)
            self.video_thread.faces_detected_signal.connect(self.update_faces_count)
            self.video_thread.start()

            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.identify_btn.setEnabled(True)
            self.auto_btn.setEnabled(True)
            self.record_btn.setEnabled(True)

            self.status_bar.showMessage("Camera started")

    def stop_camera(self):
        """Dừng camera"""
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.stop()

            self.video_label.setText("Camera Stopped\nClick 'Start Camera' to begin")

            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.identify_btn.setEnabled(False)
            self.auto_btn.setEnabled(False)
            self.record_btn.setEnabled(False)

            if self.is_auto_identify:
                self.toggle_auto_identify()

            if self.is_recording:
                self.toggle_recording()

            self.status_bar.showMessage("Camera stopped")

    def update_image(self, qt_image):
        """Update video label"""
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

        # Save frame if recording
        if self.is_recording and self.video_thread:
            frame = self.video_thread.get_current_frame()
            if frame is not None:
                self.video_frames.append(frame.copy())

        self.fps_counter += 1

    def update_faces_count(self, count):
        """Update số lượng faces"""
        self.faces_label.setText(f"Faces: {count}")

    def start_fps_counter(self):
        """Đếm FPS"""
        fps_timer = QTimer(self)
        fps_timer.timeout.connect(self.update_fps)
        fps_timer.start(1000)

    def update_fps(self):
        """Update FPS label"""
        self.fps = self.fps_counter
        self.fps_label.setText(f"FPS: {self.fps}")
        self.fps_counter = 0

    def identify_face(self):
        """Nhận diện khuôn mặt"""
        if not self.video_thread or not self.video_thread.isRunning():
            return

        frame = self.video_thread.get_current_frame()
        if frame is None:
            return

        try:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            files = {"image": ("frame.jpg", buffer.tobytes(), "image/jpeg")}

            response = requests.post(
                f"{API_URL}/api/v1/identify",
                files=files,
                headers=self._get_auth_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                faces = result.get("faces", [])

                self.identify_count += 1
                self.identify_count_label.setText(
                    f"Identifications: {self.identify_count}"
                )

                if faces:
                    face = faces[0]
                    name = face.get("user_name", "Unknown")
                    confidence = face.get("similarity", 0)

                    # Update display on frame
                    self.video_thread.set_identify_result(name, confidence)

                    self.result_label.setText(
                        f"Last Result: ✅ {name} ({confidence:.1f}%)"
                    )
                    self.result_label.setStyleSheet(
                        "font-size: 14px; font-weight: bold; color: #a6e3a1;"
                    )
                    self.status_bar.showMessage(
                        f"✅ Identified: {name} ({confidence:.1f}%)", 5000
                    )
                else:
                    # Clear identify result on frame
                    self.video_thread.clear_identify_result()
                    
                    self.result_label.setText("Last Result: ❌ No match")
                    self.result_label.setStyleSheet(
                        "font-size: 14px; font-weight: bold; color: #f38ba8;"
                    )
                    self.status_bar.showMessage("❌ No match found", 5000)
            else:
                self.status_bar.showMessage(
                    f"❌ API Error: {response.status_code}", 5000
                )

        except Exception as e:
            self.status_bar.showMessage(f"❌ Error: {str(e)}", 5000)

    def toggle_auto_identify(self):
        """Bật/tắt auto identify - Tự động nhận diện liên tục"""
        self.is_auto_identify = not self.is_auto_identify

        if self.is_auto_identify:
            self.auto_btn.setText("🔄 Auto: ON")
            self.auto_btn.setStyleSheet(
                "background-color: #a6e3a1; color: #1e1e2e; font-weight: bold; padding: 10px;"
            )
            self.auto_identify_timer = QTimer(self)
            self.auto_identify_timer.timeout.connect(self.identify_face)
            self.auto_identify_timer.start(2000)  # 2 seconds - Tự động identify mỗi 2 giây
            self.status_bar.showMessage("🔄 Auto Identify: ON - Nhận diện mỗi 2 giây", 3000)
        else:
            self.auto_btn.setText("🔄 Auto: OFF")
            self.auto_btn.setStyleSheet(
                "background-color: #45475a; color: #cdd6f4; padding: 10px;"
            )
            if self.auto_identify_timer:
                self.auto_identify_timer.stop()
            # Clear identify result when turning off
            if self.video_thread:
                self.video_thread.clear_identify_result()
            self.status_bar.showMessage("Auto Identify: OFF", 3000)

    def toggle_recording(self):
        """Bật/tắt recording video"""
        self.is_recording = not self.is_recording

        if self.is_recording:
            self.record_btn.setText("⏺️ Record: ON")
            self.record_btn.setStyleSheet(
                "background-color: #f38ba8; color: #1e1e2e; font-weight: bold; animation: blink 1s infinite;"
            )
            self.video_frames = []
            self.status_bar.showMessage("🔴 Recording started...", 0)
        else:
            self.record_btn.setText("⏺️ Record: OFF")
            self.record_btn.setStyleSheet(
                "background-color: #45475a; color: #cdd6f4; font-weight: bold;"
            )

            if len(self.video_frames) > 0:
                self.save_recorded_video()

            self.status_bar.showMessage("Recording stopped", 3000)

    def save_recorded_video(self):
        """Lưu video đã record"""
        if not self.video_frames:
            return

        from datetime import datetime

        filename = f"recorded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        try:
            height, width = self.video_frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))

            for frame in self.video_frames:
                out.write(frame)

            out.release()

            QMessageBox.information(
                self,
                "Recording Saved",
                f"✅ Video saved successfully!\n\n"
                f"File: {filename}\n"
                f"Frames: {len(self.video_frames)}\n"
                f"Location: {os.path.abspath(filename)}",
            )

            self.video_frames = []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save video: {str(e)}")

    def start_auto_refresh_database(self):
        """Tự động refresh database mỗi 2 giây"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh_people)
        self.refresh_timer.start(2000)  # 2 seconds

    def auto_refresh_people(self):
        """Auto refresh people list nếu tab đang active"""
        if self.tabs.currentIndex() == 0:  # People tab
            current_row_count = self.people_table.rowCount()
            self.load_people_list()
            new_row_count = self.people_table.rowCount()

            if new_row_count != current_row_count:
                self.auto_refresh_label.setStyleSheet(
                    "color: #a6e3a1; font-weight: bold;"
                )

    # ============ ENROLL FORM SWITCHING ============

    def show_file_enroll_form(self):
        """Hiển thị form enroll từ file"""
        self.file_enroll_group.setVisible(True)
        self.file_submit_btn.setVisible(True)
        self.camera_enroll_group.setVisible(False)
        self.camera_submit_btn.setVisible(False)

        # Update button styles
        self.enroll_from_file_btn.setStyleSheet(
            "background-color: #89b4fa; padding: 12px; font-weight: bold;"
        )
        self.enroll_from_camera_btn.setStyleSheet(
            "background-color: #45475a; padding: 12px;"
        )

    def show_camera_enroll_form(self):
        """Hiển thị form enroll từ camera"""
        self.file_enroll_group.setVisible(False)
        self.file_submit_btn.setVisible(False)
        self.camera_enroll_group.setVisible(True)
        self.camera_submit_btn.setVisible(True)

        # Update button styles
        self.enroll_from_file_btn.setStyleSheet(
            "background-color: #45475a; padding: 12px;"
        )
        self.enroll_from_camera_btn.setStyleSheet(
            "background-color: #a6e3a1; padding: 12px; font-weight: bold;"
        )

        # Check if camera is running
        if not self.video_thread or not self.video_thread.isRunning():
            QMessageBox.information(
                self,
                "Camera Required",
                "⚠️  Please start the main camera first!\n\n"
                "Go to the camera panel and click 'Start Camera'.",
            )

    def capture_face_from_camera(self):
        """Capture khuôn mặt từ camera đang chạy"""
        if not self.video_thread or not self.video_thread.isRunning():
            QMessageBox.warning(
                self, "Camera Not Running", "❌ Please start the camera first!"
            )
            return

        # Get current frame
        frame = self.video_thread.get_current_frame()
        if frame is None:
            QMessageBox.warning(self, "Error", "❌ Cannot get frame from camera")
            return

        # Check if there's a face
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        if len(faces) == 0:
            QMessageBox.warning(
                self,
                "No Face Detected",
                "❌ No face detected in frame!\n\nPlease position your face in front of the camera.",
            )
            return

        if len(faces) > 1:
            reply = QMessageBox.question(
                self,
                "Multiple Faces",
                f"⚠️  Detected {len(faces)} faces!\n\nDo you want to continue with the largest face?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        # Draw rectangle on the captured face
        display_frame = frame.copy()
        for x, y, w, h in faces:
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                display_frame,
                "Captured!",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        # Store the captured frame
        self.captured_frame = frame.copy()

        # Display in preview
        rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            320, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.capture_label.setPixmap(scaled_pixmap)

        self.status_bar.showMessage(
            f"✅ Captured {len(faces)} face(s)! Fill the form and click Register.", 5000
        )

    def enroll_from_camera(self):
        """Đăng ký người từ ảnh đã capture"""
        if self.captured_frame is None:
            QMessageBox.warning(
                self,
                "No Photo",
                "❌ Please capture a photo first!\n\nClick 'Capture Face from Camera' button.",
            )
            return

        user_name = self.camera_name_edit.text().strip()
        if not user_name:
            QMessageBox.warning(self, "Warning", "❌ Name is required!")
            return

        try:
            # Encode frame to JPEG and convert to base64
            _, buffer = cv2.imencode(
                ".jpg", self.captured_frame, [cv2.IMWRITE_JPEG_QUALITY, 95]
            )
            image_base64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

            # Sanitize user_id - remove non-ASCII characters
            user_id = re.sub(r"[^a-zA-Z0-9_-]", "", user_name.lower().replace(" ", "_"))
            if not user_id:
                user_id = f"user_{uuid.uuid4().hex[:8]}"

            # Helper function to sanitize text fields
            def sanitize_text(text):
                """Remove non-ASCII characters or encode"""
                if not text:
                    return ""
                # Keep only ASCII printable characters
                return "".join(c if ord(c) < 128 else "" for c in text).strip()

            # Prepare multipart form data as backend expects
            self.status_bar.showMessage("⏳ Enrolling... Please wait...", 0)

            # Create form data matching backend EnrollmentRequest model
            form_data = {
                "user_name": user_name,  # Backend expects user_name not user_id
                "gender": sanitize_text(self.camera_gender_combo.currentText()),
                "birth_year": str(self.camera_birth_spin.value()),
                "hometown": sanitize_text(self.camera_hometown_edit.text().strip()),
                "residence": sanitize_text(self.camera_residence_edit.text().strip()),
            }

            # Prepare image file
            files = {
                "image": ("photo.jpg", buffer.tobytes(), "image/jpeg")
            }

            headers = self._get_auth_headers()

            response = requests.post(
                f"{API_URL}/api/v1/enroll",
                data=form_data,  # Form data
                files=files,      # Image file
                headers=headers,
                timeout=30,
            )

            # Handle both 200 (sync) and 202 (async) responses
            if response.status_code in [200, 202]:
                result = response.json()
                
                # Check if enrollment actually succeeded (important!)
                if result.get("success") == False:
                    # API returned 200 but enrollment failed (AWS not configured)
                    message = result.get("message", "Enrollment failed")
                    QMessageBox.warning(
                        self,
                        "AWS Configuration Required",
                        f"{message}\n\n"
                        f"📋 To enable face enrollment, you need:\n\n"
                        f"1️⃣ AWS Rekognition collection\n"
                        f"2️⃣ AWS S3 bucket for images\n"
                        f"3️⃣ AWS DynamoDB tables\n"
                        f"4️⃣ Configure .env file with credentials\n"
                        f"5️⃣ Restart backend with full app.py\n\n"
                        f"💡 For now, the UI works but real face recognition needs AWS.",
                    )
                    self.status_bar.showMessage("⚠️ AWS services not configured", 5000)
                    return
                
                tracking_id = result.get("tracking_id", "N/A")
                status = result.get("status", "COMPLETED")

                if response.status_code == 202:
                    # Async processing
                    QMessageBox.information(
                        self,
                        "Processing",
                        f"✅ Enrollment request accepted!\n\n"
                        f"Tracking ID: {tracking_id}\n"
                        f"Status: {status}\n\n"
                        f"Your face is being processed by AWS Lambda.\n"
                        f"Please wait a moment and refresh the People list.",
                    )
                else:
                    # Sync processing - real success with AWS
                    QMessageBox.information(
                        self,
                        "Success",
                        f"✅ Enrolled successfully!\n\n"
                        f"Person ID: {result.get('person_id', 'N/A')}\n"
                        f"Face ID: {result.get('face_id', 'N/A')}",
                    )

                # Clear form and preview
                self.camera_name_edit.clear()
                self.camera_gender_combo.setCurrentIndex(0)
                self.camera_birth_spin.setValue(1990)
                self.camera_hometown_edit.clear()
                self.camera_residence_edit.clear()
                self.capture_label.clear()
                self.capture_label.setText("Click 'Capture' to take photo")
                self.captured_frame = None

                # Refresh people list
                self.load_people_list()
                self.status_bar.showMessage("✅ Enrolled successfully!", 5000)
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"❌ API Error: {response.status_code}\n{response.text}",
                )
                self.status_bar.showMessage("❌ Enrollment failed", 5000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ {str(e)}")
            self.status_bar.showMessage("❌ Error occurred", 5000)

    # ============ DATABASE FUNCTIONS ============

    def load_people_list(self):
        """Load danh sách người"""
        try:
            response = requests.get(
                f"{API_URL}/api/v1/people", headers=self._get_auth_headers(), timeout=10
            )

            if response.status_code == 200:
                people = response.json()  # API returns array directly
                if isinstance(people, dict):  # Handle both formats
                    people = people.get("people", [])

                self.people_table.setRowCount(len(people))
                
                # Populate table rows
                for i, person in enumerate(people):
                    self.people_table.setItem(
                        i, 0, QTableWidgetItem(person.get("user_name", "N/A"))
                    )
                    self.people_table.setItem(
                        i, 1, QTableWidgetItem(person.get("folder_name", "N/A"))
                    )
                    self.people_table.setItem(
                        i, 2, QTableWidgetItem(person.get("gender", "N/A"))
                    )
                    self.people_table.setItem(
                        i, 3, QTableWidgetItem(str(person.get("birth_year", "N/A")))
                    )

                    # Action buttons
                    action_widget = QWidget()
                    action_layout = QHBoxLayout()
                    action_layout.setContentsMargins(5, 2, 5, 2)

                    view_btn = QPushButton("👁️")
                    view_btn.setMaximumWidth(40)
                    view_btn.clicked.connect(
                        lambda checked, f=person.get("folder_name"): self.view_person(f)
                    )

                    edit_btn = QPushButton("✏️")
                    edit_btn.setMaximumWidth(40)
                    edit_btn.clicked.connect(
                        lambda checked, f=person.get("folder_name"): self.edit_person(f)
                    )

                    delete_btn = QPushButton("🗑️")
                    delete_btn.setMaximumWidth(40)
                    delete_btn.setStyleSheet("background-color: #f38ba8;")
                    delete_btn.clicked.connect(
                        lambda checked, f=person.get("folder_name"): self.delete_person(
                            f
                        )
                    )

                    action_layout.addWidget(view_btn)
                    action_layout.addWidget(edit_btn)
                    action_layout.addWidget(delete_btn)

                    # Add open folder button
                    folder_btn = QPushButton("📁")
                    folder_btn.setMaximumWidth(40)
                    folder_btn.setStyleSheet(
                        "background-color: #f9e2af; color: #1e1e2e;"
                    )
                    folder_btn.clicked.connect(
                        lambda checked, f=person.get(
                            "folder_name"
                        ): self.open_person_folder(f)
                    )
                    action_layout.addWidget(folder_btn)

                    action_widget.setLayout(action_layout)

                    self.people_table.setCellWidget(i, 4, action_widget)

                self.status_bar.showMessage(f"✅ Loaded {len(people)} people", 3000)
            else:
                # Don't show error dialog - just status message
                self.people_table.setRowCount(0)
                self.status_bar.showMessage(f"⚠️ API Error {response.status_code} - Showing empty list", 5000)

        except Exception as e:
            # Don't crash - just show error in status bar
            self.people_table.setRowCount(0)
            self.status_bar.showMessage(f"⚠️ Error: {str(e)}", 5000)

    def view_person(self, folder_name):
        """Xem chi tiết người"""
        try:
            response = requests.get(
                f"{API_URL}/api/v1/people/{folder_name}",
                headers=self._get_auth_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                person = response.json()

                detail_text = f"""
👤 Name: {person.get('user_name', 'N/A')}
📁 Folder: {person.get('folder_name', 'N/A')}
⚧  Gender: {person.get('gender', 'N/A')}
🎂 Birth Year: {person.get('birth_year', 'N/A')}
🏠 Hometown: {person.get('hometown', 'N/A')}
📍 Residence: {person.get('residence', 'N/A')}
📊 Embeddings: {person.get('num_embeddings', 0)}
📅 Created: {person.get('created_at', 'N/A')}
🔄 Updated: {person.get('updated_at', 'N/A')}
                """

                QMessageBox.information(
                    self, f"👤 {person.get('user_name', 'N/A')}", detail_text.strip()
                )
            else:
                QMessageBox.warning(self, "Error", "Person not found")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def edit_person(self, folder_name):
        """Sửa thông tin người"""
        dialog = EditPersonDialog(folder_name, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_people_list()

    def delete_person(self, folder_name):
        """Xóa người"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"⚠️  Are you sure you want to delete '{folder_name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                response = requests.delete(
                    f"{API_URL}/api/v1/people/{folder_name}", headers=self._get_auth_headers(), timeout=10
                )

                if response.status_code == 200:
                    QMessageBox.information(self, "Success", "✅ Deleted successfully!")
                    self.load_people_list()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete")

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def browse_image(self):
        """Chọn file ảnh"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_name:
            self.image_path_edit.setText(file_name)

    def enroll_person(self):
        """Đăng ký người mới"""
        image_path = self.image_path_edit.text().strip()
        user_name = self.enroll_name_edit.text().strip()

        if not image_path or not user_name:
            QMessageBox.warning(self, "Warning", "Image and Name are required!")
            return

        if not os.path.exists(image_path):
            QMessageBox.warning(self, "Warning", "Image file not found!")
            return

        try:
            # Read and encode image to base64
            with open(image_path, "rb") as img_file:
                image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

            # Sanitize user_id - remove non-ASCII characters
            user_id = re.sub(r"[^a-zA-Z0-9_-]", "", user_name.lower().replace(" ", "_"))
            if not user_id:
                user_id = f"user_{uuid.uuid4().hex[:8]}"

            # Helper function to sanitize text fields
            def sanitize_text(text):
                """Remove non-ASCII characters"""
                if not text:
                    return ""
                return "".join(c if ord(c) < 128 else "" for c in text).strip()

            # Send as JSON
            payload = {
                "user_id": user_id,
                "image_base64": image_base64,
                "metadata": {
                    "name": user_name,  # Keep original
                    "gender": sanitize_text(self.enroll_gender_combo.currentText()),
                    "birth_year": str(self.enroll_birth_spin.value()),
                    "hometown": sanitize_text(self.enroll_hometown_edit.text().strip()),
                    "residence": sanitize_text(
                        self.enroll_residence_edit.text().strip()
                    ),
                },
            }

            headers = self._get_auth_headers()
            headers["Content-Type"] = "application/json"

            response = requests.post(
                f"{API_URL}/api/v1/enroll",
                json=payload,
                headers=headers,
                timeout=30,
            )

            # Handle both 200 (sync) and 202 (async) responses
            if response.status_code in [200, 202]:
                result = response.json()
                
                # Check if enrollment actually succeeded
                if result.get("success") == False:
                    # API returned 200 but enrollment failed (AWS not configured)
                    message = result.get("message", "Enrollment failed")
                    QMessageBox.warning(
                        self,
                        "AWS Configuration Required",
                        f"{message}\n\n"
                        f"📋 To enable face enrollment:\n\n"
                        f"1️⃣ Configure AWS Rekognition, S3, DynamoDB\n"
                        f"2️⃣ Set credentials in .env file\n"
                        f"3️⃣ Restart backend with full app.py",
                    )
                    self.status_bar.showMessage("⚠️ AWS not configured", 5000)
                    return
                
                tracking_id = result.get("tracking_id", "N/A")
                status = result.get("status", "COMPLETED")

                if response.status_code == 202:
                    # Async processing
                    QMessageBox.information(
                        self,
                        "Processing",
                        f"✅ Enrollment request accepted!\n\n"
                        f"Tracking ID: {tracking_id}\n"
                        f"Status: {status}\n\n"
                        f"Your face is being processed by AWS Lambda.\n"
                        f"Please wait a moment and refresh the People list.",
                    )
                else:
                    # Sync processing - real success with AWS
                    QMessageBox.information(
                        self,
                        "Success",
                        f"✅ Enrolled successfully!\n\n"
                        f"Person ID: {result.get('person_id', 'N/A')}\n"
                        f"Face ID: {result.get('face_id', 'N/A')}",
                    )

                # Clear form
                self.image_path_edit.clear()
                self.enroll_name_edit.clear()
                self.enroll_gender_combo.setCurrentIndex(0)
                self.enroll_birth_spin.setValue(1990)
                self.enroll_hometown_edit.clear()
                self.enroll_residence_edit.clear()

                # Refresh people list
                self.load_people_list()
            else:
                QMessageBox.warning(
                    self, "Error", f"API Error: {response.status_code}\n{response.text}"
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_stats(self):
        """Load thống kê"""
        try:
            response = requests.get(f"{API_URL}/api/v1/stats", headers=self._get_auth_headers(), timeout=10)

            if response.status_code == 200:
                stats = response.json()

                stats_text = f"""
═══════════════════════════════════════
         📊 DATABASE STATISTICS
═══════════════════════════════════════

👥 Total People: {stats.get('total_people', 0)}

📊 Total Embeddings: {stats.get('total_embeddings', 0)}

💾 Storage Size: {stats.get('storage_size_mb', 0):.2f} MB

🔍 Identifications (Session): {self.identify_count}

🔄 Last Updated: {stats.get('last_updated', 'N/A')}

═══════════════════════════════════════
                """

                self.stats_text.setPlainText(stats_text.strip())
                self.status_bar.showMessage("Stats loaded successfully", 3000)
            else:
                QMessageBox.warning(self, "Error", f"API Error: {response.status_code}")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, event):
        """Cleanup khi đóng app"""
        if self.is_recording:
            reply = QMessageBox.question(
                self,
                "Recording Active",
                "Video recording is active. Save before exit?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )

            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.Yes:
                self.save_recorded_video()

        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.stop()

        if self.refresh_timer:
            self.refresh_timer.stop()

        event.accept()

    # ============ ADVANCED FEATURES ============

    def browse_video(self):
        """Chọn file video cho enroll"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_name:
            self.video_path_edit.setText(file_name)

    def browse_recog_video(self):
        """Chọn file video cho recognition"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_name:
            self.recog_video_path_edit.setText(file_name)

    def enroll_from_video(self):
        """Enroll từ video file - extract tất cả frames"""
        video_path = self.video_path_edit.text().strip()

        if not video_path:
            QMessageBox.warning(self, "Warning", "Please select a video file!")
            return

        if not os.path.exists(video_path):
            QMessageBox.warning(self, "Warning", "Video file not found!")
            return

        # Ask for person info
        dialog = VideoEnrollDialog(video_path, self)
        dialog.exec_()

    def recognize_from_video(self):
        """Nhận diện từ video file"""
        video_path = self.recog_video_path_edit.text().strip()

        if not video_path:
            QMessageBox.warning(self, "Warning", "Please select a video file!")
            return

        if not os.path.exists(video_path):
            QMessageBox.warning(self, "Warning", "Video file not found!")
            return

        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            results = {}
            frame_count = 0

            self.advanced_results.setPlainText("Processing video...\n")

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                if frame_count % 30 == 0:  # Process every 30 frames
                    _, buffer = cv2.imencode(".jpg", frame)
                    files = {"image": ("frame.jpg", buffer.tobytes(), "image/jpeg")}

                    try:
                        response = requests.post(
                            f"{API_URL}/api/v1/identify", files=files, headers=self._get_auth_headers(), timeout=5
                        )
                        if response.status_code == 200:
                            data = response.json()
                            matches = data.get("matches", [])
                            if matches:
                                name = matches[0].get("person_name", "Unknown")
                                results[name] = results.get(name, 0) + 1
                    except requests.RequestException:
                        self.status_bar.showMessage(
                            "Network error during video recognition", 3000
                        )

                    progress = (frame_count / total_frames) * 100
                    self.advanced_results.append(
                        f"Progress: {progress:.1f}% - Frame {frame_count}/{total_frames}"
                    )
                    QApplication.processEvents()

            cap.release()

            # Display results
            report = "\n\n📊 Recognition Results:\n" + "=" * 50 + "\n"
            for name, count in sorted(
                results.items(), key=lambda x: x[1], reverse=True
            ):
                report += f"👤 {name}: {count} detections\n"

            self.advanced_results.append(report)
            self.status_bar.showMessage("Video processing completed!", 5000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process video: {str(e)}")

    def generate_organization_report(self):
        """Tạo báo cáo tổ chức file"""
        faces_dir = os.path.join(os.getcwd(), "faces")

        if not os.path.exists(faces_dir):
            QMessageBox.information(self, "Info", "No faces directory found")
            return

        report = "📁 File Organization Report\n" + "=" * 60 + "\n\n"

        total_people = 0
        total_files = 0

        for person_folder in os.listdir(faces_dir):
            person_path = os.path.join(faces_dir, person_folder)
            if os.path.isdir(person_path):
                files = [
                    f
                    for f in os.listdir(person_path)
                    if f.lower().endswith((".jpg", ".png", ".jpeg", ".mp4", ".avi"))
                ]
                if files:
                    total_people += 1
                    total_files += len(files)
                    report += f"👤 {person_folder}:\n"
                    report += f"   📊 Total files: {len(files)}\n"

                    images = [
                        f
                        for f in files
                        if f.lower().endswith((".jpg", ".png", ".jpeg"))
                    ]
                    videos = [f for f in files if f.lower().endswith((".mp4", ".avi"))]

                    if images:
                        report += f"   🖼️  Images: {len(images)}\n"
                    if videos:
                        report += f"   🎥 Videos: {len(videos)}\n"
                    report += "\n"

        report += "=" * 60 + "\n"
        report += "📊 Summary:\n"
        report += f"   Total people: {total_people}\n"
        report += f"   Total files: {total_files}\n"
        report += f"   Average files per person: {total_files/total_people if total_people > 0 else 0:.1f}\n"

        self.advanced_results.setPlainText(report)
        self.status_bar.showMessage("Report generated successfully!", 3000)


# ============ EDIT DIALOG ============
class EditPersonDialog(QDialog):
    def __init__(self, folder_name, parent=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.parent_window = parent
        self.initUI()
        self.load_data()

    def initUI(self):
        self.setWindowTitle(f"✏️ Edit Person: {self.folder_name}")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Form
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("👤 Name:", self.name_edit)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["", "Nam", "Nữ"])
        form_layout.addRow("⚧ Gender:", self.gender_combo)

        self.birth_spin = QSpinBox()
        self.birth_spin.setRange(1900, 2024)
        form_layout.addRow("🎂 Birth Year:", self.birth_spin)

        self.hometown_edit = QLineEdit()
        form_layout.addRow("🏠 Hometown:", self.hometown_edit)

        self.residence_edit = QLineEdit()
        form_layout.addRow("📍 Residence:", self.residence_edit)

        layout.addLayout(form_layout)

        # Buttons
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_changes)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def load_data(self):
        """Load dữ liệu hiện tại"""
        try:
            response = requests.get(
                f"{API_URL}/api/v1/people/{self.folder_name}", headers=self.parent_window._get_auth_headers(), timeout=10
            )

            if response.status_code == 200:
                person = response.json()

                self.name_edit.setText(person.get("user_name", ""))

                gender = person.get("gender", "")
                index = self.gender_combo.findText(gender)
                if index >= 0:
                    self.gender_combo.setCurrentIndex(index)

                birth_year = person.get("birth_year")
                if birth_year:
                    self.birth_spin.setValue(int(birth_year))

                self.hometown_edit.setText(person.get("hometown", ""))
                self.residence_edit.setText(person.get("residence", ""))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def save_changes(self):
        """Lưu thay đổi"""
        data = {
            "user_name": self.name_edit.text().strip(),
            "gender": self.gender_combo.currentText(),
            "birth_year": str(self.birth_spin.value()),
            "hometown": self.hometown_edit.text().strip(),
            "residence": self.residence_edit.text().strip(),
        }

        # Remove empty fields
        data = {k: v for k, v in data.items() if v}

        try:
            response = requests.put(
                f"{API_URL}/api/v1/people/{self.folder_name}", json=data, headers=self.parent_window._get_auth_headers(), timeout=10
            )

            if response.status_code == 200:
                QMessageBox.information(self, "Success", "✅ Updated successfully!")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", f"API Error: {response.status_code}")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ============ VIDEO ENROLL DIALOG ============
class VideoEnrollDialog(QDialog):
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.parent_window = parent
        self.initUI()

    def initUI(self):
        self.setWindowTitle("🎥 Enroll from Video")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(f"Video: {os.path.basename(self.video_path)}")
        info.setStyleSheet("font-weight: bold; color: #89b4fa; padding: 10px;")
        layout.addWidget(info)

        # Form
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Required")
        form_layout.addRow("👤 Name:", self.name_edit)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["", "Nam", "Nữ"])
        form_layout.addRow("⚧ Gender:", self.gender_combo)

        self.birth_spin = QSpinBox()
        self.birth_spin.setRange(1900, 2024)
        self.birth_spin.setValue(1990)
        form_layout.addRow("🎂 Birth Year:", self.birth_spin)

        self.hometown_edit = QLineEdit()
        form_layout.addRow("🏠 Hometown:", self.hometown_edit)

        self.residence_edit = QLineEdit()
        form_layout.addRow("📍 Residence:", self.residence_edit)

        layout.addLayout(form_layout)

        # Progress
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(150)
        layout.addWidget(self.progress_text)

        # Buttons
        btn_layout = QHBoxLayout()

        process_btn = QPushButton("🎥 Process Video & Enroll")
        process_btn.setStyleSheet("background-color: #a6e3a1; padding: 12px;")
        process_btn.clicked.connect(self.process_video)

        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.reject)

        btn_layout.addWidget(process_btn)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def process_video(self):
        """Xử lý video và enroll tất cả frames có face"""
        user_name = self.name_edit.text().strip()
        if not user_name:
            QMessageBox.warning(self, "Warning", "Name is required!")
            return

        try:
            cap = cv2.VideoCapture(self.video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

            enrolled_count = 0
            processed_count = 0

            self.progress_text.append(f"Processing {total_frames} frames...\n")

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                processed_count += 1

                # Detect faces
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

                if len(faces) > 0 and processed_count % 30 == 0:  # Every 30 frames
                    # Enroll this frame
                    _, buffer = cv2.imencode(".jpg", frame)
                    files = {"image": ("frame.jpg", buffer.tobytes(), "image/jpeg")}
                    data = {
                        "user_name": user_name,
                        "gender": self.gender_combo.currentText(),
                        "birth_year": str(self.birth_spin.value()),
                        "hometown": self.hometown_edit.text().strip(),
                        "residence": self.residence_edit.text().strip(),
                    }

                    try:
                        headers = self.parent_window._get_auth_headers()
                        response = requests.post(
                            f"{API_URL}/api/v1/enroll",
                            files=files,
                            data=data,
                            headers=headers,
                            timeout=30,
                        )
                        if response.status_code == 200:
                            enrolled_count += 1
                            self.progress_text.append(
                                f"✅ Frame {processed_count}: Enrolled successfully"
                            )
                        else:
                            self.progress_text.append(
                                f"❌ Frame {processed_count}: Failed"
                            )
                    except Exception as e:
                        self.progress_text.append(
                            f"⚠️ Frame {processed_count}: Error - {str(e)}"
                        )

                    QApplication.processEvents()

                if processed_count % 100 == 0:
                    progress = (processed_count / total_frames) * 100
                    self.progress_text.append(f"Progress: {progress:.1f}%")
                    QApplication.processEvents()

            cap.release()

            self.progress_text.append(f"\n{'='*50}")
            self.progress_text.append("✅ Completed!")
            self.progress_text.append(f"Total frames processed: {processed_count}")
            self.progress_text.append(f"Successfully enrolled: {enrolled_count}")

            QMessageBox.information(
                self,
                "Success",
                f"Video processing completed!\n\n"
                f"Total frames: {processed_count}\n"
                f"Enrolled: {enrolled_count}",
            )

            # Refresh parent
            if self.parent_window:
                self.parent_window.load_people_list()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process video: {str(e)}")


# ============ MAIN ============
def main():
    app = QApplication(sys.argv)

    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Show main window directly without login
    window = FaceRecognitionApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
