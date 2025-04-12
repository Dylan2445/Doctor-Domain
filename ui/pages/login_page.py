from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, 
                            QGridLayout, QLineEdit, QPushButton, QHBoxLayout,
                            QMessageBox, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import json
import requests
import urllib3
from pathlib import Path
from typing import Callable, Optional
from ..state import AuthState

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LoginPage(QWidget):
    def __init__(self, on_login: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.auth_state = AuthState.instance()
        self.on_login = on_login
        self.config_path = Path(__file__).parent.parent.parent / 'config' / 'login_settings.json'
        self.config_path.parent.mkdir(exist_ok=True)
        self.setup_ui()
        self.load_login_settings()
        self.auth_state.add_listener(self.update_ui_state)
        self.update_ui_state()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        self.header = QLabel("Login")
        self.header.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
            padding-bottom: 15px;
        """)
        self.main_layout.addWidget(self.header)

        # Create containers for both states
        self.login_container = self.create_login_container()
        self.logged_in_container = self.create_logged_in_container()
        
        self.main_layout.addWidget(self.login_container)
        self.main_layout.addWidget(self.logged_in_container)
        self.main_layout.addStretch()

    def create_logged_in_container(self):
        container = QFrame()
        container.setFixedWidth(600)
        container.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                padding: 20px 30px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        # Account Status Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        status_icon = QLabel("🟢")  # Green circle emoji
        status_icon.setStyleSheet("""
            font-size: 14px;
            margin-right: 8px;
        """)
        
        status_text = QLabel("Active Session")
        status_text.setStyleSheet("""
            font-size: 14px;
            color: #059669;
        """)
        
        header_layout.addWidget(status_icon)
        header_layout.addWidget(status_text)
        header_layout.addStretch()

        logout_btn = QPushButton("Logout")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #EF4444;
                border: 1px solid #EF4444;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #FEE2E2;
            }
        """)
        logout_btn.clicked.connect(self.handle_logout)
        header_layout.addWidget(logout_btn)
        
        layout.addWidget(header_widget)

        # Account Parameters Section
        params_section = QFrame()
        params_section.setStyleSheet("""
            QFrame {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        params_layout = QVBoxLayout(params_section)
        params_layout.setSpacing(16)
        params_layout.setContentsMargins(20, 20, 20, 20)

        # Section title
        section_title = QLabel("Connection Parameters")
        section_title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1E293B;
        """)
        params_layout.addWidget(section_title)

        # Parameters grid
        params_grid = QWidget()
        grid_layout = QGridLayout(params_grid)
        grid_layout.setSpacing(12)
        grid_layout.setColumnStretch(1, 1)

        # Define fields to show
        fields = [
            ("Server", "🌐"),
            ("Library ID", "📚"),
            ("Username", "👤"),
            ("Client ID", "🔑")
        ]

        for row, (field, icon) in enumerate(fields):
            # Create field container
            field_container = QWidget()
            field_layout = QVBoxLayout(field_container)
            field_layout.setSpacing(4)
            field_layout.setContentsMargins(0, 0, 0, 0)

            # Label with icon
            label = QLabel(f"{icon} {field}")
            label.setStyleSheet("""
                color: #64748B;
                font-size: 13px;
            """)
            
            # Value
            value = QLabel(self.login_inputs[field].text() if field in self.login_inputs else "")
            value.setStyleSheet("""
                color: #1E293B;
                font-size: 14px;
                font-weight: 500;
            """)
            
            field_layout.addWidget(label)
            field_layout.addWidget(value)
            
            grid_layout.addWidget(field_container, row, 0)

        params_layout.addWidget(params_grid)

        # Add edit button at the bottom of parameters section
        edit_btn = QPushButton("Edit Connection Parameters")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 13px;
                width: 100%;
            }
            QPushButton:hover {
                background: #2563EB;
            }
        """)
        edit_btn.clicked.connect(self.switch_to_edit_mode)
        params_layout.addWidget(edit_btn)

        layout.addWidget(params_section)
        layout.addStretch()

        return container

    def switch_to_edit_mode(self):
        """Switch from logged in view to edit mode"""
        self.login_container.setVisible(True)
        self.logged_in_container.setVisible(False)
        self.header.setText("Edit Parameters")

    def create_login_container(self):
        form_container = QFrame()
        form_container.setFixedWidth(600)
        form_container.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                padding: 20px 30px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        form_container.setGraphicsEffect(shadow)

        form_layout = QGridLayout(form_container)
        form_layout.setSpacing(12)
        form_layout.setColumnStretch(1, 1)
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(8)

        self.login_inputs = {}
        fields = [
            ("Server", "", "Connect to your organization's server", "Example: workserver.example.com"),
            ("Library ID", "", "Specify your library system identifier", "Example: Active"),
            ("Username", "", "Enter your domain username", "Example: john.doe"),
            ("Password", "", "Enter your domain password", "Keep Secure"),
            ("Client ID", "", "Your assigned client identifier", "From administrator"),
            ("Client Secret", "", "Your client authentication secret", "Optional")
        ]

        for i, (label_text, default, description, tip) in enumerate(fields):
            row = i * 2
            self.add_form_field(form_layout, row, label_text, description, tip)

        btn_container = self.create_button_container()
        form_layout.addWidget(btn_container, len(fields) * 2, 0, 1, 2, Qt.AlignmentFlag.AlignRight)
        
        return form_container

    def update_ui_state(self):
        """Update UI based on login state"""
        is_logged_in = self.auth_state.is_logged_in
        self.login_container.setVisible(not is_logged_in)
        self.logged_in_container.setVisible(is_logged_in)
        self.header.setText("Account" if is_logged_in else "Login")

    def handle_logout(self):
        self.auth_state.logout()
        self.show_message("Success", "You have been logged out successfully.", QMessageBox.Icon.Information)

    def add_form_field(self, layout, row, label_text, description, tip):
        label = QLabel(label_text)
        label.setFixedWidth(120)
        label.setStyleSheet("""
            color: #1E293B;
            font-weight: 600;
            font-size: 14px;
            padding: 8px 0;
        """)
        
        input_field = QLineEdit()
        input_field.setFixedHeight(36)
        input_field.setPlaceholderText(tip)
        if label_text == "Password":
            input_field.setEchoMode(QLineEdit.EchoMode.Password)
        
        input_field.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                background: white;
                color: #1E293B;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
            QLineEdit::placeholder {
                color: #94A3B8;
                opacity: 0.8;
            }
        """)
        
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #64748B;
            font-size: 12px;
            padding: 0 0 12px 0;
            min-height: 16px;
        """)
        
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(input_field, row, 1)
        layout.addWidget(desc_label, row + 1, 1)
        
        self.login_inputs[label_text] = input_field

    def create_button_container(self):
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setSpacing(12)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        login_btn = QPushButton("Login")
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setStyleSheet("""
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
        
        clear_btn = QPushButton("Clear")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #EF4444;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #DC2626;
            }
        """)

        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(clear_btn)

        login_btn.clicked.connect(self.attempt_login)
        clear_btn.clicked.connect(self.clear_login_settings)

        return btn_container

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