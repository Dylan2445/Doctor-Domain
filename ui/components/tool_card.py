from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QPushButton, 
                          QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import subprocess
from pathlib import Path
from ..state import AuthState
import json
from scripts.user_retriever import UserRetriever

class ToolCard(QFrame):
    def __init__(self, title, description, icon_path, script_path):
        super().__init__()
        self.script_path = script_path
        self.auth_state = AuthState.instance()
        
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # Adjust shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(12, 8, 12, 8)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 19px;
            font-weight: 600;
            color: #1E293B;
        """)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            color: #64748B;
            font-size: 13px;
            line-height: 130%;
            margin-bottom: 2px;
        """)
        desc_label.setWordWrap(True)
        
        self.run_btn = QPushButton("Coming Soon" if script_path is None else "Run Tool")
        self.run_btn.setEnabled(script_path is not None)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 5px;
                font-weight: 500;
                font-size: 13px;
                margin-top: 2px;
            }
            QPushButton:disabled {
                background: #94A3B8;
            }
            QPushButton:hover:!disabled {
                background: #2563EB;
            }
        """)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if script_path:
            self.run_btn.clicked.connect(self.handle_run)
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(self.run_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def handle_run(self):
        """Handle the run button click based on the script type"""
        if not self.auth_state.is_logged_in:
            self.show_error("Not Logged In", "Please log in first to use this tool.")
            return
            
        if not self.auth_state.access_token:
            self.show_error("Authentication Error", "No access token found. Please log in again.")
            return
            
        try:
            # Load settings to get server and library ID
            config_path = Path(__file__).parent.parent.parent / 'config' / 'login_settings.json'
            if not config_path.exists():
                self.show_error("Configuration Error", "Login settings not found. Please configure your account first.")
                return
                
            with open(config_path) as f:
                settings = json.load(f)
                
            server = settings.get('Server')
            library_id = settings.get('Library ID')
            
            if not all([server, library_id]):
                self.show_error("Configuration Error", "Missing server or library ID in settings.")
                return
                
            if str(self.script_path).endswith('email_sanitizer.py'):
                # For sanitizer, first get user list
                retriever = UserRetriever(server, self.auth_state.access_token, library_id)
                try:
                    users = retriever.get_user_list()
                    # Store users in a temporary file for the sanitizer script
                    temp_path = Path(__file__).parent.parent.parent / 'temp_users.json'
                    with open(temp_path, 'w') as f:
                        json.dump(users, f)
                    # Now run the actual sanitizer script
                    subprocess.run(["python", self.script_path], check=True)
                except Exception as e:
                    self.show_error("Error", f"Failed to retrieve users: {str(e)}")
                finally:
                    # Clean up temp file
                    if temp_path.exists():
                        temp_path.unlink()
            else:
                # For other scripts, just run them directly
                subprocess.run(["python", self.script_path], check=True)
                
        except Exception as e:
            self.show_error("Error", f"Failed to run tool: {str(e)}")

    def show_error(self, title: str, message: str):
        """Show an error message box"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #1E293B;
            }
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #2563EB;
            }
        """)
        msg.exec()