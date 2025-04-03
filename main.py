import sys
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect,
                                QHBoxLayout, QStackedWidget)
    from PyQt6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QPoint
    from PyQt6.QtGui import QColor, QPalette, QIcon, QFont
    print("Using PyQt6")
except ImportError:
    print("Error: Could not load PyQt6.")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

import subprocess
from pathlib import Path

class NavigationButton(QPushButton):
    def __init__(self, text, icon_path=None):
        super().__init__()
        self.setText(text)
        if icon_path:
            self.setIcon(QIcon(str(Path(__file__).parent / "icons" / icon_path)))
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                border: none;
                text-align: left;
                padding: 12px 15px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 8px;
                margin: 2px 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            QPushButton[Active=true] {
                background: #3B82F6;
                color: white;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Doctor Domain")
        self.setMinimumSize(1000, 600)
        
        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Side navigation
        nav_panel = QWidget()
        nav_panel.setStyleSheet("""
            background: #1E293B;
            min-width: 250px;
            max-width: 250px;
        """)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)

        # Logo section
        logo_widget = QWidget()
        logo_widget.setStyleSheet("background: #0F172A;")
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(20, 15, 20, 15)  # Adjusted padding
        logo = QLabel("🏥 Doctor Domain")
        logo.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: 600;
        """)
        logo_layout.addWidget(logo)
        nav_layout.addWidget(logo_widget)
        nav_layout.addSpacing(10)

        # Navigation buttons
        self.email_tools_btn = NavigationButton("📧 Email Tools", "email.png")
        self.settings_btn = NavigationButton("⚙️ Settings", "settings.png")
        self.coming_soon_btn = NavigationButton("🔜 Coming Soon", "soon.png")
        
        nav_layout.addWidget(self.email_tools_btn)
        nav_layout.addWidget(self.coming_soon_btn)  # Add before settings
        nav_layout.addWidget(self.settings_btn)
        nav_layout.addStretch()

        # Main content area
        content_area = QWidget()
        content_area.setStyleSheet("background: #F1F5F9;")
        content_layout = QVBoxLayout(content_area)
        
        # Stacked widget for different pages
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        # Add pages
        self.email_tools_page = self.create_email_tools_page()
        self.settings_page = self.create_settings_page()
        self.coming_soon_page = self.create_coming_soon_page()
        
        self.stack.addWidget(self.email_tools_page)
        self.stack.addWidget(self.coming_soon_page)
        self.stack.addWidget(self.settings_page)

        # Connect buttons
        self.email_tools_btn.clicked.connect(lambda: self.switch_page(0))
        self.coming_soon_btn.clicked.connect(lambda: self.switch_page(1))
        self.settings_btn.clicked.connect(lambda: self.switch_page(2))

        # Add to main layout
        layout.addWidget(nav_panel)
        layout.addWidget(content_area)

        # Initial state
        self.email_tools_btn.setProperty("Active", True)
        self.email_tools_btn.style().unpolish(self.email_tools_btn)
        self.email_tools_btn.style().polish(self.email_tools_btn)

    def create_email_tools_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)  # Reduced from 15

        # Header
        header = QLabel("Email Management Tools")
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
            padding-bottom: 5px;
        """)
        layout.addWidget(header)

        # Cards
        cards_widget = QWidget()
        cards_layout = QVBoxLayout(cards_widget)  # Changed from QHBoxLayout to QVBoxLayout
        cards_layout.setSpacing(15)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        # Function cards container
        functions_widget = QWidget()
        functions_layout = QHBoxLayout(functions_widget)
        functions_layout.setSpacing(15)
        functions_layout.setContentsMargins(0, 0, 0, 0)

        sanitizer_card = self.create_tool_card(
            "Email Sanitizer 🧼",
            "Finds and updates any user email addresses that are not intended domains.",
            "sanitize.png",
            "./scripts/email_sanitizer.ps1"
        )
        injector_card = self.create_tool_card(
            "Email Injector 💉",
            "Updates all accounts missing an email address by assigning a placeholder domain.",
            "inject.png",
            "./scripts/email_injector.ps1"
        )

        functions_layout.addWidget(sanitizer_card)
        functions_layout.addWidget(injector_card)
        cards_layout.addWidget(functions_widget)

        # Coming soon card
        coming_soon_card = self.create_tool_card(
            "Additional Tools Coming Soon ⏳",
            "New Features Coming Soon!",
            "soon.png",
            None
        )
        cards_layout.addWidget(coming_soon_card)

        layout.addWidget(cards_widget)
        layout.addStretch()

        return page

    def create_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("Settings")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: 600;
            color: #1E293B;
        """)
        layout.addWidget(header)
        
        config_card = self.create_tool_card(
            "Configure Environment",
            "Set up prerequisites and permissions for the email management tools.",
            "config.png",
            "./scripts/configure_env.ps1"
        )
        
        layout.addWidget(config_card)
        layout.addStretch()
        return page

    def create_coming_soon_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel("Coming Soon")
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
            padding-bottom: 5px;
        """)
        layout.addWidget(header)

        coming_soon_card = self.create_tool_card(
            "More Features Coming Soon",
            "Stay tuned for additional tools and features that will enhance your email management capabilities.",
            "soon.png",
            None
        )
        
        layout.addWidget(coming_soon_card)
        layout.addStretch()
        return page

    def create_tool_card(self, title, description, icon_path, script_path):
        card = QFrame()
        card.setStyleSheet("""
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
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setSpacing(2)  # Reduced from 4
        layout.setContentsMargins(12, 8, 12, 8)  # Reduced vertical margins
        
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
        
        run_btn = QPushButton("Coming Soon" if script_path is None else "Run Tool")
        run_btn.setEnabled(script_path is not None)
        run_btn.setStyleSheet("""
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
        run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if script_path:
            run_btn.clicked.connect(lambda: self.run_script(script_path))
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(run_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        return card

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        
        # Update button states
        buttons = [self.email_tools_btn, self.coming_soon_btn, self.settings_btn]
        for i, btn in enumerate(buttons):
            btn.setProperty("Active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def run_script(self, script_path):
        try:
            subprocess.run(["powershell", "-File", script_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running script: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
