import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QFrame, QGraphicsDropShadowEffect,
                            QHBoxLayout, QStackedWidget, QPushButton)
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer
from PyQt6.QtGui import QColor, QPalette, QIcon, QFont
from pathlib import Path

from ui.navigation import NavigationButton
from ui.pages.email_tools_page import EmailToolsPage
from ui.pages.login_page import LoginPage
from ui.pages.settings_page import SettingsPage
from ui.pages.logs_page import LogsPage
from ui.components.log_overlay import LogOverlay
from ui.state import AuthState
from ui.utils import log_message

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
        
        # Regular logs button (no toggle)
        self.logs_btn = NavigationButton("📋 Logs", "logs.png")
        
        nav_layout.addWidget(self.email_tools_btn)
        nav_layout.addWidget(self.login_btn)
        nav_layout.addWidget(self.settings_btn)
        nav_layout.addStretch()  # Push logs to bottom
        nav_layout.addWidget(self.logs_btn)  # No more toggle container
        nav_layout.addSpacing(10)  # Add spacing at bottom

        # Main content area
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: white;")
        content_layout = QVBoxLayout(self.content_widget)
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
            'logs': LogsPage()
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        # Initialize log overlay
        self.log_overlay = LogOverlay(self.content_widget)
        self.log_overlay.hide()  # Initially hidden
        self.log_overlay.setGeometry(0, 0, 400, 300)  # Initial size
        self.log_overlay.connect_full_logs_button(lambda: self.switch_page('logs'))

        # Setup permanent log handle at the bottom
        # We'll create the handle now, but postpone positioning until after window is shown
        self.setup_log_handle()
        self.log_handle.hide()  # Hide initially

        # Connect buttons
        self.email_tools_btn.clicked.connect(lambda: self.switch_page('email'))
        self.login_btn.clicked.connect(lambda: self.switch_page('login'))
        self.settings_btn.clicked.connect(lambda: self.switch_page('settings'))
        self.logs_btn.clicked.connect(lambda: self.switch_page('logs'))

        # Add to main layout
        layout.addWidget(nav_panel)
        layout.addWidget(self.content_widget)

        # Initial state
        self.email_tools_btn.setProperty("Active", True)
        self.email_tools_btn.style().unpolish(self.email_tools_btn)
        self.email_tools_btn.style().polish(self.email_tools_btn)
        
        # Use a short timer to position the log handle after the window is shown
        # This ensures the window has its final size before positioning the handle
        QTimer.singleShot(100, self.properly_position_log_handle)
        
    def setup_log_handle(self):
        """Setup a permanent log handle at the bottom of the screen"""
        # Create a permanent log handle at the bottom of the screen
        self.log_handle = QFrame(self.content_widget)
        self.log_handle.setObjectName("logHandle")
        self.apply_log_handle_style()
        
        # Add minimal handle layout with just the drag indicator
        handle_layout = QHBoxLayout(self.log_handle)
        handle_layout.setContentsMargins(10, 4, 10, 4)
        
        # Drag indicator
        drag_indicator = QFrame()
        drag_indicator.setFixedSize(60, 4)
        drag_indicator.setStyleSheet("""
            background-color: #64748B;
            border-radius: 2px;
        """)
        
        handle_layout.addWidget(drag_indicator, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Position the handle at the bottom
        self.update_log_handle_position()
        
        # Connect handle to toggle log overlay
        self.log_handle.mousePressEvent = self.handle_click
    
    def apply_log_handle_style(self):
        """Apply consistent styling to the log handle"""
        self.log_handle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.log_handle.setStyleSheet("""
            #logHandle {
                background-color: rgba(203, 213, 225, 0.8);
                border-radius: 6px 6px 0 0;
                border: 1px solid #E2E8F0;
                border-bottom: none;
            }
            #logHandle:hover {
                background-color: rgba(148, 163, 184, 0.9);
            }
        """)
        
    def handle_click(self, event):
        """Handle click on the log handle"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_log_overlay()
    
    def update_log_handle_position(self):
        """Update the position of the log handle during resize"""
        handle_width = min(400, self.content_widget.width() - 40)
        self.log_handle.setFixedSize(handle_width, 26)
        self.log_handle.move(
            (self.content_widget.width() - handle_width) // 2,
            self.content_widget.height() - 26
        )
        
    def properly_position_log_handle(self):
        """Properly position the log handle after the window is shown and sized"""
        # Position the handle at the bottom of the screen
        handle_width = min(400, self.content_widget.width() - 40)
        self.log_handle.setFixedSize(handle_width, 26)
        self.log_handle.move(
            (self.content_widget.width() - handle_width) // 2,
            self.content_widget.height() - 26
        )
        
        # Only show if not on logs page
        current_page = self.stack.currentWidget()
        if current_page != self.pages['logs']:
            self.log_handle.show()
        
    def toggle_log_overlay(self):
        """Toggle the visibility of the log overlay"""
        if self.log_overlay.isVisible():
            self.log_overlay.hide()
            # Show the handle when overlay is hidden, but only if not on logs page
            current_page = self.stack.currentWidget()
            if current_page != self.pages['logs']:
                self.log_handle.show()
                self.apply_log_handle_style()
        else:
            # Hide the handle when overlay is shown
            self.log_handle.hide()
            
            # Position at bottom of the window and show expanded immediately
            self.log_overlay.setGeometry(
                20,  # Small margin from left
                self.content_widget.height() - self.log_overlay.expanded_height,  # Position for expanded view
                self.content_widget.width() - 40,  # Almost full width with margins
                self.log_overlay.expanded_height  # Start with full expanded height
            )
            self.log_overlay.show()
            
            # Immediately set to expanded state
            self.log_overlay.is_expanded = True
            self.log_overlay.content_container.show()
            self.log_overlay.refresh_log()  # Refresh logs
        
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
        # If switching to logs page, make sure log overlay is closed
        if page_id == 'logs' and self.log_overlay.isVisible():
            self.log_overlay.hide()
            
        self.stack.setCurrentWidget(self.pages[page_id])
        
        # Update button states
        buttons = {
            'email': self.email_tools_btn,
            'login': self.login_btn,
            'settings': self.settings_btn,
            'logs': self.logs_btn
        }
        
        for pid, btn in buttons.items():
            btn.setProperty("Active", pid == page_id)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
        # Show or hide the log handle based on the current page AND overlay visibility
        if page_id == 'logs' or self.log_overlay.isVisible():
            self.log_handle.hide()
        else:
            self.log_handle.show()
            self.apply_log_handle_style()  # Ensure consistent styling
            
    def resizeEvent(self, event):
        """Adjust log overlay position when window is resized"""
        if self.log_overlay.isVisible():
            if self.log_overlay.is_expanded:
                # Keep the expanded height when expanded
                self.log_overlay.setGeometry(
                    20,  # Small margin from left
                    self.content_widget.height() - self.log_overlay.expanded_height,  
                    self.content_widget.width() - 40,  # Almost full width with margins
                    self.log_overlay.expanded_height
                )
            else:
                # Just show the handle when collapsed
                self.log_overlay.setGeometry(
                    20,  # Small margin from left
                    self.content_widget.height() - self.log_overlay.collapsed_height,  
                    self.content_widget.width() - 40,  # Almost full width with margins
                    self.log_overlay.collapsed_height
                )
        
        # Update log handle position
        self.update_log_handle_position()
        
        # Only show the log handle if we're not on the logs page and the overlay isn't visible
        current_page = self.stack.currentWidget()
        if current_page != self.pages['logs'] and not self.log_overlay.isVisible():
            self.log_handle.show()
            self.apply_log_handle_style()  # Ensure consistent styling
        elif current_page == self.pages['logs'] or self.log_overlay.isVisible():
            self.log_handle.hide()
            
        super().resizeEvent(event)
            
    def closeEvent(self, event):
        """Clean up when window is closed"""
        self.auth_state.remove_listener(self.on_auth_state_changed)
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Log application startup
    log_message("Application starting...")
    
    window = MainWindow()
    window.show()
    
    # Ensure login page has a chance to try auto-login if credentials are saved
    # This forces the proper initialization of the login page's auto-login feature
    window.switch_page('login')
    
    # Then switch back to the main Email Tools page
    QTimer.singleShot(100, lambda: window.switch_page('email'))
    
    # Log successful startup
    log_message("Application UI initialized and displayed")
    
    sys.exit(app.exec())
