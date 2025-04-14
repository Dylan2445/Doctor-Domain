import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QFrame, QGraphicsDropShadowEffect,
                            QHBoxLayout, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette, QIcon, QFont

from ui.navigation import NavigationButton
from ui.pages.email_tools_page import EmailToolsPage
from ui.pages.login_page import LoginPage
from ui.pages.settings_page import SettingsPage
from ui.pages.coming_soon_page import ComingSoonPage
from ui.state import AuthState

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Doctor Domain")
        self.setMinimumSize(1000, 600)
        
        # Get auth state instance
        self.auth_state = AuthState.instance()
        self.auth_state.add_listener(self.on_auth_state_changed)
        
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
        logo_layout.setContentsMargins(20, 15, 20, 15)
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
        self.login_btn = NavigationButton("🔑 Account", "login.png")
        self.settings_btn = NavigationButton("⚙️ Settings", "settings.png")
        self.coming_soon_btn = NavigationButton("🔜 Coming Soon", "soon.png")
        
        nav_layout.addWidget(self.email_tools_btn)
        nav_layout.addWidget(self.login_btn)
        nav_layout.addWidget(self.settings_btn)
        nav_layout.addWidget(self.coming_soon_btn)
        nav_layout.addStretch()

        # Main content area
        content_area = QWidget()
        content_area.setStyleSheet("background: white;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Stacked widget for different pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: white;")
        content_layout.addWidget(self.stack)

        # Create and add pages
        self.pages = {
            'email': EmailToolsPage(),
            'login': LoginPage(on_login=self.on_login_success),
            'settings': SettingsPage(),
            'coming_soon': ComingSoonPage()
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        # Connect buttons
        self.email_tools_btn.clicked.connect(lambda: self.switch_page('email'))
        self.login_btn.clicked.connect(lambda: self.switch_page('login'))
        self.settings_btn.clicked.connect(lambda: self.switch_page('settings'))
        self.coming_soon_btn.clicked.connect(lambda: self.switch_page('coming_soon'))

        # Add to main layout
        layout.addWidget(nav_panel)
        layout.addWidget(content_area)

        # Initial state
        self.email_tools_btn.setProperty("Active", True)
        self.email_tools_btn.style().unpolish(self.email_tools_btn)
        self.email_tools_btn.style().polish(self.email_tools_btn)
        
    def on_login_success(self, access_token: str):
        """Called by the login page when login is successful"""
        self.auth_state.login(access_token)
        
    def handle_auth_button_click(self):
        """Handle click on the login/logout button"""
        if self.auth_state.is_logged_in:
            self.auth_state.logout()
            self.switch_page('login')
        else:
            self.switch_page('login')
            
    def on_auth_state_changed(self):
        """Update UI when auth state changes"""
        # No longer changing the button text based on login state
        pass

    def switch_page(self, page_id):
        self.stack.setCurrentWidget(self.pages[page_id])
        
        # Update button states
        buttons = {
            'email': self.email_tools_btn,
            'login': self.login_btn,
            'settings': self.settings_btn,
            'coming_soon': self.coming_soon_btn
        }
        
        for pid, btn in buttons.items():
            btn.setProperty("Active", pid == page_id)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
    def closeEvent(self, event):
        """Clean up when window is closed"""
        self.auth_state.remove_listener(self.on_auth_state_changed)
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
