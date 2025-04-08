from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, 
                            QGridLayout, QLineEdit, QPushButton, QHBoxLayout,
                            QMessageBox, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import json
from pathlib import Path

class LoginPage(QWidget):
    def __init__(self):
        super().__init__()
        self.config_path = Path(__file__).parent.parent.parent / 'config' / 'login_settings.json'
        self.config_path.parent.mkdir(exist_ok=True)
        self.setup_ui()
        self.load_login_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel("Login Settings")
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
            padding-bottom: 15px;
        """)
        layout.addWidget(header)

        form_container = self.create_form_container()
        layout.addWidget(form_container)
        layout.addStretch()

    def create_form_container(self):
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

        save_btn = QPushButton("Save Settings")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
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

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(clear_btn)

        save_btn.clicked.connect(self.save_login_settings)
        clear_btn.clicked.connect(self.clear_login_settings)

        return btn_container

    def save_login_settings(self):
        settings = {}
        for label, input_field in self.login_inputs.items():
            settings[label] = input_field.text()
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(settings, f, indent=4)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("Settings saved successfully")
            msg.setWindowTitle("Success")
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
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(f"Error saving settings: {str(e)}")
            msg.setWindowTitle("Error")
            msg.exec()

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