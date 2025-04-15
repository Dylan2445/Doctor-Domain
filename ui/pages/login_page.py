from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, 
                            QGridLayout, QLineEdit, QPushButton, QHBoxLayout,
                            QMessageBox, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
import json
import requests
import urllib3
from pathlib import Path
from typing import Callable, Optional
from ..state import AuthState

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LoginPage(QWidget):
    def __init__(self, on_login: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.auth_state = AuthState.instance()
        self.on_login = on_login
        self.config_path = Path(__file__).parent.parent.parent / 'config' / 'login_settings.json'
        self.config_path.parent.mkdir(exist_ok=True)
        self.login_inputs = {}
        self.setup_ui()
        self.load_login_settings()
        self.auth_state.add_listener(self.update_ui_state)
        self.update_ui_state()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 16, 25, 20)
        main_layout.setSpacing(12)

        # Header with status
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        header = QLabel("Account Settings")
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
        """)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 4px;
            background: #F1F5F9;
        """)
        
        header_layout.addWidget(header)
        header_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch()
        
        main_layout.addWidget(header_container)
        self.login_form = self.create_login_form()
        main_layout.addWidget(self.login_form)
        main_layout.addStretch()

    def create_login_form(self):
        form = QFrame()
        form.setFixedWidth(580)
        form.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 10px;  # Slightly reduced radius
            }
        """)

        layout = QVBoxLayout(form)
        layout.setSpacing(12)  # Reduced spacing
        layout.setContentsMargins(0, 0, 0, 0)

        # Main content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)  # Reduced spacing
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Create sections using modern panels
        sections_data = [
            ("Connection Details", [
                ("Server", "workserver.example.com"),
                ("Customer ID", "Enter customer ID"),
                ("Library ID", "Active")
            ]), 
            ("Login Credentials", [
                ("Username", "john.doe"),
                ("Password", "Enter password", True)
            ]),
            ("API Settings", [
                ("Client ID", "From administrator"),
                ("Client Secret", "Optional")
            ])
        ]

        for section_title, fields in sections_data:
            panel = self.create_panel(section_title, fields)
            content_layout.addWidget(panel)

        layout.addWidget(content)

        # Bottom action panel
        action_panel = QWidget()
        action_panel.setStyleSheet("""
            QWidget {
                background: #F8FAFC;
                border-top: 1px solid #E2E8F0;
            }
        """)
        action_layout = QHBoxLayout(action_panel)
        action_layout.setContentsMargins(24, 20, 24, 20)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedSize(100, 38)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                color: #DC2626;
                border: 1.5px solid #DC2626;
                border-radius: 6px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #FEE2E2;
            }
        """)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setFixedSize(100, 38)
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2563EB;
            }
        """)

        action_layout.addStretch()
        action_layout.addWidget(self.clear_btn)
        action_layout.addWidget(self.connect_btn)

        self.clear_btn.clicked.connect(self.clear_login_settings)
        self.connect_btn.clicked.connect(self.handle_connection)

        layout.addWidget(action_panel)
        return form

    def create_panel(self, title: str, fields: list) -> QWidget:
        panel = QWidget()
        layout = QGridLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 12, 20, 12)

        # Title at the top
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #0F172A; margin-bottom: 4px;")
        layout.addWidget(title_label, 0, 0, 1, 2)

        # Add fields starting from row 1
        for row, (label_text, placeholder, *opts) in enumerate(fields, start=1):
            # Label styling with fixed width
            label = QLabel(f"{label_text}:")
            label.setFixedWidth(110)  # Fixed width for alignment
            label.setStyleSheet("""
                font-size: 13px;
                color: #475569;
                margin-right: 6px;
            """)
            
            # Input field styling
            input_field = QLineEdit()
            input_field.setPlaceholderText(placeholder)
            if opts and opts[0]:
                input_field.setEchoMode(QLineEdit.EchoMode.Password)

            input_field.setStyleSheet("""
                QLineEdit {
                    border: 1.5px solid #E2E8F0;
                    border-radius: 5px;
                    padding: 6px 10px;
                    background: white;
                    color: #0F172A;
                    font-size: 13px;
                    margin: 2px 0;
                    min-height: 16px;
                }
                QLineEdit:focus {
                    border: 2px solid #3B82F6;
                }
            """)

            # Add to grid with proper alignment
            layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(input_field, row, 1)
            
            self.login_inputs[label_text] = input_field

        # Set column stretching for proper alignment
        layout.setColumnStretch(1, 1)
        layout.setColumnMinimumWidth(0, 120)  # Ensure consistent label column width
        return panel

    def handle_connection(self):
        if self.auth_state.is_logged_in:
            self.handle_logout()
        else:
            self.attempt_login()

    def update_ui_state(self):
        is_logged_in = self.auth_state.is_logged_in
        
        # Update status label with new styling
        self.status_label.setText("Connected" if is_logged_in else "Disconnected")
        self.status_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 4px;
            color: {'#059669' if is_logged_in else '#94A3B8'};
            background: {'#ECFDF5' if is_logged_in else '#F1F5F9'};
        """)

        # Update button text and style
        self.connect_btn.setText("Disconnect" if is_logged_in else "Connect")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 14px;
                background: %s;
                color: %s;
                border: %s;
                border-radius: 5px;
                font-weight: 500;
                min-width: 90px;
            }
            QPushButton:hover {
                background: %s;
            }
        """ % (
            'white' if is_logged_in else '#3B82F6',
            '#DC2626' if is_logged_in else 'white',
            '1.5px solid #DC2626' if is_logged_in else 'none',
            '#FEE2E2' if is_logged_in else '#2563EB'
        ))

        # Update input fields
        for input_field in self.login_inputs.values():
            input_field.setReadOnly(is_logged_in)
            input_field.setStyleSheet("""
                QLineEdit {
                    border: 1.5px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 8px 12px;
                    background: %s;
                    color: #1E293B;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 2px solid #3B82F6;
                }
            """ % ('#F8FAFC' if is_logged_in else 'white'))

        # Show/hide clear button
        self.clear_btn.setVisible(not is_logged_in)

    def handle_logout(self):
        self.auth_state.logout()
        self.show_message("Success", "You have been logged out successfully.", QMessageBox.Icon.Information)

    def attempt_login(self):
        # Get all input values
        server = self.login_inputs["Server"].text()
        username = self.login_inputs["Username"].text()
        password = self.login_inputs["Password"].text()
        client_id = self.login_inputs["Client ID"].text()
        client_secret = self.login_inputs["Client Secret"].text().strip()

        # Validate required fields
        if not all([server, username, password, client_id]):
            self.show_message("Error", "Please fill in all required fields.", QMessageBox.Icon.Warning)
            return

        try:
            # Set up the signin parameters
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            # Build parameters for the request body
            body_params = {
                'username': username,
                'password': password,
                'grant_type': 'password',
                'client_id': client_id,
                'scope': 'admin'
            }

            # Only add client_secret if it's not blank
            if client_secret:
                body_params['client_secret'] = client_secret

            url = f'https://{server}/auth/oauth2/token'
            
            # Create URL string for display (for debugging/error messages)
            param_str = '&'.join([f"{k}={v}" for k, v in body_params.items()])

            # Send the POST request with parameters in the body
            response = requests.post(
                url,
                headers=headers,
                data=body_params,  # Use data instead of params to send in body
                verify=False
            )

            if response.status_code == 200:
                access_token = response.json()['access_token']
                self.save_login_settings()  # Save successful login details
                self.show_message("Success", "Login successful!", QMessageBox.Icon.Information)
                if self.on_login:
                    self.on_login(access_token)
                self.auth_state.login(access_token)
                return access_token
            else:
                self.show_message(
                    "Login Failed", 
                    f"Sign in unsuccessful.\nURL: {url}\nBody Parameters:\n{param_str}\n\nStatus code: {response.status_code}\n{response.text}", 
                    QMessageBox.Icon.Critical
                )

        except requests.exceptions.RequestException as e:
            self.show_message(
                "Error", 
                f"Connection error:\nURL: {url}\nBody Parameters:\n{param_str}\n\nError: {str(e)}", 
                QMessageBox.Icon.Critical
            )
        except Exception as e:
            self.show_message(
                "Error", 
                f"Unexpected error:\nURL: {url}\nBody Parameters:\n{param_str}\n\nError: {str(e)}", 
                QMessageBox.Icon.Critical
            )

    def show_message(self, title, text, icon=QMessageBox.Icon.Information):
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setText(text)
        msg.setWindowTitle(title)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #1E293B;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #2563EB;
            }
        """)
        msg.exec()

    def save_login_settings(self):
        settings = {}
        for label, input_field in self.login_inputs.items():
            settings[label] = input_field.text()
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            self.show_message("Error", f"Error saving settings: {str(e)}", QMessageBox.Icon.Critical)

    def load_login_settings(self):
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    settings = json.load(f)
                for label, value in settings.items():
                    if label in self.login_inputs:
                        self.login_inputs[label].setText(value)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def clear_login_settings(self):
        for input_field in self.login_inputs.values():
            input_field.clear()