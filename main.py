import sys
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QVBoxLayout, QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect)
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor, QPalette
    print("Using PyQt6")
except ImportError:
    try:
        from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                                     QVBoxLayout, QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect)
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor, QPalette
        print("Using PySide6")
    except ImportError:
        print("Error: Could not load either PyQt6 or PySide6.")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

import subprocess

class FunctionCard(QFrame):
    def __init__(self, title, description, script_path):
        super().__init__()
        self.script_path = script_path
        self.setFixedHeight(180)  # Even more compact
        self.setGraphicsEffect(self.create_shadow())
        self.setStyleSheet("""
            QFrame {
                background: linear-gradient(145deg, #FFFFFF, #F8F9FA);
                border: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 12px;
            }
            QLabel#title {
                color: #1A365D;
                font-family: 'Segoe UI', system-ui, -apple-system;
                font-weight: 600;
                font-size: 20px;
                letter-spacing: -0.2px;
            }
            QLabel#description {
                color: #4A5568;
                font-family: 'Segoe UI', system-ui, -apple-system;
                font-size: 13.5px;
                line-height: 140%;
                font-weight: 400;
            }
            QPushButton {
                background-color: #3182CE;
                color: white;
                border: none;
                padding: 7px 18px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Segoe UI', system-ui, -apple-system;
            }
            QPushButton:hover {
                background-color: #2B6CB0;
                transition: background-color 0.2s;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setObjectName("title")
        description_label = QLabel(description)
        description_label.setObjectName("description")
        description_label.setWordWrap(True)
        run_button = QPushButton("Run Script")
        run_button.setFixedWidth(140)
        run_button.setCursor(Qt.CursorShape.PointingHandCursor)
        run_button.clicked.connect(self.run_script)
        layout.addWidget(title_label)
        layout.addWidget(description_label, 1)
        layout.addWidget(run_button, 0, Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)

    def create_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 15))
        return shadow

    def run_script(self):
        try:
            subprocess.run(["powershell", "-File", self.script_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running script: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Doctor Domain")
        self.setMinimumSize(850, 580)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#F7FAFC"))
        self.setPalette(palette)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(35, 25, 35, 25)
        main_layout.setSpacing(12)

        # Title section
        title = QLabel("Doctor Domain")
        title.setStyleSheet("""
            font-family: 'Segoe UI', system-ui, -apple-system;
            font-size: 28px;
            font-weight: 600;
            color: #1A365D;
            letter-spacing: -0.3px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Email Management Tools")
        subtitle.setStyleSheet("""
            font-family: 'Segoe UI', system-ui, -apple-system;
            font-size: 14px;
            color: #4A5568;
            margin-top: -5px;
            font-weight: 400;
            letter-spacing: 0.2px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Cards container
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(15)

        # Add cards
        email_sanitizer = FunctionCard(
            "Email Sanitizer",
            "Standardizes email domains by identifying and modifying non-compliant email addresses. Helps prevent duplicate accounts during cloud migration by appending .ext to non-compliant addresses.",
            "./scripts/email_sanitizer.ps1"
        )
        email_injector = FunctionCard(
            "Email Injector",
            "Automatically detects and updates blank email accounts by analyzing existing user domains in the environment and applying consistent domain patterns.",
            "./scripts/email_injector.ps1"
        )

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(8)  # Reduced spacing
        main_layout.addWidget(email_sanitizer)
        main_layout.addSpacing(4)  # Minimal gap between cards
        main_layout.addWidget(email_injector)
        main_layout.addStretch()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
