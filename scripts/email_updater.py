import os
import json
import csv
import time
import datetime
import requests
import urllib3
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                          QLineEdit, QMessageBox, QProgressBar, QApplication,
                          QTableWidget, QTableWidgetItem, QFrame, QHBoxLayout,
                          QHeaderView, QDialog, QDialogButtonBox, QTextEdit,
                          QCheckBox, QComboBox, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from ui.utils import log_function_execution, create_styled_message_box, log_message as system_log_message

# Disable SSL warnings for older server compatibility
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EmailUpdaterPage(QWidget):
    """Page that handles the updating of sanitized user emails"""
    back_clicked = pyqtSignal()
    
    def __init__(self, sanitized_users=None):
        super().__init__()
        # Store sanitized users data
        self.sanitized_users = sanitized_users or []
        
        # Logs directory
        self.log_dir = Path(__file__).parent / "Logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file_path = self.log_dir / "updatescriptlog.txt"
        
        # Auth and API settings
        self.server = ""
        self.library = ""
        self.auth_token = ""
        self.customer_id = ""
        self.headers = {
            "Accept": "*/*",
            "Content-Type": "application/json"
        }
        
        # API rate limiting settings
        self.pause_time = 60  # seconds
        self.rate_limit = 10  # API calls before pausing
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for the email update page"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 16, 25, 20)
        main_layout.setSpacing(12)

        # Header section
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Update User Emails")
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
        """)
        
        self.status_label = QLabel("Ready to update emails")
        self.status_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 4px;
            background: #F1F5F9;
            color: #64748B;
        """)
        
        header_layout.addWidget(title)
        header_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch()
        
        main_layout.addWidget(header_container)
        
        # Main content panel
        content_panel = QFrame()
        content_panel.setFrameShape(QFrame.Shape.StyledPanel)
        content_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)
        
        # Description text
        description = QLabel("This tool will update the email addresses for external users identified in the sanitization process.")
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: #475569;
            font-size: 14px;
            margin-bottom: 10px;
        """)
        content_layout.addWidget(description)
        
        # Server connection panel
        connection_panel = QFrame()
        connection_panel.setStyleSheet("""
            background-color: #F8FAFC;
            border-radius: 8px;
            padding: 16px;
        """)
        
        connection_layout = QVBoxLayout(connection_panel)
        connection_layout.setSpacing(16)
        
        connection_title = QLabel("Server Connection")
        connection_title.setStyleSheet("font-weight: 600; color: #0F172A; font-size: 16px;")
        connection_layout.addWidget(connection_title)
        
        # Hostname input
        hostname_layout = QHBoxLayout()
        hostname_label = QLabel("Hostname:")
        hostname_label.setMinimumWidth(100)
        hostname_label.setStyleSheet("color: #334155; font-size: 14px;")
        
        self.hostname_input = QLineEdit()
        self.hostname_input.setPlaceholderText("Enter hostname (e.g., server.example.com)")
        self.hostname_input.setStyleSheet("""
            padding: 8px;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
            font-size: 14px;
        """)
        
        hostname_layout.addWidget(hostname_label)
        hostname_layout.addWidget(self.hostname_input)
        connection_layout.addLayout(hostname_layout)
        
        # Library input (conditional)
        library_layout = QHBoxLayout()
        library_label = QLabel("Library Name:")
        library_label.setMinimumWidth(100)
        library_label.setStyleSheet("color: #334155; font-size: 14px;")
        
        self.library_input = QLineEdit()
        self.library_input.setPlaceholderText("Enter library name (only for on-premise)")
        self.library_input.setStyleSheet("""
            padding: 8px;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
            font-size: 14px;
        """)
        
        library_layout.addWidget(library_label)
        library_layout.addWidget(self.library_input)
        connection_layout.addLayout(library_layout)
        
        # Connection test button
        test_connection_btn = QPushButton("Test Connection")
        test_connection_btn.setStyleSheet("""
            QPushButton {
                background-color: #EFF6FF;
                color: #3B82F6;
                border: 1px solid #DBEAFE;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #DBEAFE;
            }
        """)
        test_connection_btn.clicked.connect(self.test_connection)
        connection_layout.addWidget(test_connection_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        content_layout.addWidget(connection_panel)
        
        # Users preview table
        preview_label = QLabel("Users to Update")
        preview_label.setStyleSheet("font-weight: 600; color: #0F172A; font-size: 16px; margin-top: 8px;")
        content_layout.addWidget(preview_label)
        
        # Table to show users that will be updated
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["User ID", "Name", "Original Email", "New Email"])
        self.users_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #F1F5F9;
                padding: 8px;
                border: 1px solid #E2E8F0;
                font-weight: 600;
                color: #334155;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #F1F5F9;
            }
        """)
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only
        
        # Populate table with data if available
        if self.sanitized_users:
            self.populate_users_table()
        
        content_layout.addWidget(self.users_table)
        
        # Progress bar
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 8, 0, 8)
        
        self.progress_label = QLabel("Ready to process")
        self.progress_label.setStyleSheet("color: #475569; font-size: 14px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                background-color: #F1F5F9;
                text-align: center;
                padding: 2px;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 3px;
            }
        """)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_container.setVisible(False)  # Hide initially
        content_layout.addWidget(self.progress_container)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("Back")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 10px 16px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        self.back_btn.clicked.connect(self.back_clicked)
        
        self.update_btn = QPushButton("Update Emails")
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:disabled {
                background-color: #94A3B8;
                color: #F1F5F9;
            }
        """)
        self.update_btn.clicked.connect(self.confirm_update)
        self.update_btn.setEnabled(False)  # Disabled until connection is tested
        
        actions_layout.addWidget(self.back_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.update_btn)
        
        content_layout.addLayout(actions_layout)
        
        # Add content panel to main layout
        main_layout.addWidget(content_panel)
    
    def populate_users_table(self):
        """Populate the table with sanitized user data"""
        external_users = [user for user in self.sanitized_users if user.get("Classification") == "External"]
        self.users_table.setRowCount(len(external_users))
        
        for i, user in enumerate(external_users):
            # Set data for each column
            self.users_table.setItem(i, 0, QTableWidgetItem(str(user.get("UserID", ""))))
            self.users_table.setItem(i, 1, QTableWidgetItem(str(user.get("FullName", ""))))
            
            # Original email
            original_email = str(user.get("Email", ""))
            email_item = QTableWidgetItem(original_email)
            self.users_table.setItem(i, 2, email_item)
            
            # New email
            new_email = str(user.get("NewEmail", ""))
            new_email_item = QTableWidgetItem(new_email)
            new_email_item.setForeground(QColor("#059669"))  # Green for new email
            self.users_table.setItem(i, 3, new_email_item)
        
        self.status_label.setText(f"Found {len(external_users)} external users to update")
    
    def test_connection(self):
        """Test connection to the server"""
        self.server = self.hostname_input.text().strip()
        self.library = self.library_input.text().strip()
        
        if not self.server:
            QMessageBox.warning(self, "Missing Information", "Please enter a hostname.")
            return
        
        # Clear any previous token
        self.auth_token = ""
        self.customer_id = ""
        
        # Show login dialog
        if not self.show_login_dialog():
            return
        
        self.status_label.setText("Testing connection...")
        QApplication.processEvents()
        
        try:
            # Attempt to sign in
            success = self.sign_in()
            if not success:
                QMessageBox.critical(self, "Connection Failed", "Failed to authenticate with the server.")
                self.status_label.setText("Connection failed")
                return
            
            # Get customer ID
            success = self.get_customer_id()
            if not success:
                QMessageBox.critical(self, "Connection Failed", "Failed to retrieve customer information.")
                self.status_label.setText("Connection failed")
                return
            
            # Connection successful
            QMessageBox.information(self, "Connection Successful", 
                                  f"Successfully connected to {self.server} and authenticated.")
            self.status_label.setText("Connection successful")
            self.update_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Error connecting to server: {str(e)}")
            self.status_label.setText("Connection error")
            self.log_message(f"Connection error: {str(e)}")
    
    def show_login_dialog(self):
        """Show dialog to collect login credentials"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Login")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # Dialog content
        content = QLabel("Enter your API credentials:")
        content.setStyleSheet("font-size: 14px; color: #334155;")
        layout.addWidget(content)
        
        # Form fields
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        
        # Username field
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setMinimumWidth(100)
        username_label.setStyleSheet("color: #334155;")
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setStyleSheet("""
            padding: 8px;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
        """)
        
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        form_layout.addLayout(username_layout)
        
        # Password field
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        password_label.setMinimumWidth(100)
        password_label.setStyleSheet("color: #334155;")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            padding: 8px;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
        """)
        
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)
        
        # Client ID field
        client_id_layout = QHBoxLayout()
        client_id_label = QLabel("Client ID:")
        client_id_label.setMinimumWidth(100)
        client_id_label.setStyleSheet("color: #334155;")
        
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Enter client ID")
        self.client_id_input.setStyleSheet("""
            padding: 8px;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
        """)
        
        client_id_layout.addWidget(client_id_label)
        client_id_layout.addWidget(self.client_id_input)
        form_layout.addLayout(client_id_layout)
        
        # Client Secret field
        client_secret_layout = QHBoxLayout()
        client_secret_label = QLabel("Client Secret:")
        client_secret_label.setMinimumWidth(100)
        client_secret_label.setStyleSheet("color: #334155;")
        
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("Enter client secret")
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_secret_input.setStyleSheet("""
            padding: 8px;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
        """)
        
        client_secret_layout.addWidget(client_secret_label)
        client_secret_layout.addWidget(self.client_secret_input)
        form_layout.addLayout(client_secret_layout)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton[text="OK"] {
                background-color: #3B82F6;
                color: white;
                border: none;
            }
            QPushButton[text="OK"]:hover {
                background-color: #2563EB;
            }
            QPushButton[text="Cancel"] {
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
            }
            QPushButton[text="Cancel"]:hover {
                background-color: #E2E8F0;
            }
        """)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog and get result
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted
    
    def sign_in(self):
        """Authenticate with the server and get auth token"""
        try:
            # Create OAuth2 payload
            payload = {
                "username": self.username_input.text(),
                "password": self.password_input.text(),
                "grant_type": "password",
                "client_id": self.client_id_input.text(),
                "client_secret": self.client_secret_input.text(),
                "scope": "admin"
            }
            
            headers = {
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Send authentication request
            response = requests.post(
                f"https://{self.server}/auth/oauth2/token",
                headers=headers,
                data=payload,
                verify=False  # Disable SSL verification for compatibility
            )
            
            # Check if response is successful
            if response.status_code == 200:
                response_data = response.json()
                self.auth_token = response_data.get("access_token")
                
                if self.auth_token:
                    # Update headers with token
                    self.headers["X-Auth-Token"] = self.auth_token
                    self.log_message(f"Successfully authenticated with {self.server}")
                    return True
            
            # If we got here, authentication failed
            error_message = f"Authentication failed with status code: {response.status_code}"
            if response.text:
                error_message += f" - {response.text}"
            
            self.log_message(error_message)
            return False
            
        except Exception as e:
            self.log_message(f"Authentication error: {str(e)}")
            return False
    
    def get_customer_id(self):
        """Get customer ID from the server"""
        try:
            response = requests.get(
                f"https://{self.server}/api",
                headers=self.headers,
                verify=False
            )
            
            if response.status_code == 200:
                response_data = response.json()
                self.customer_id = response_data.get("data", {}).get("user", {}).get("customer_id")
                
                if self.customer_id:
                    self.log_message(f"Successfully retrieved customer ID: {self.customer_id}")
                    return True
            
            # If we got here, getting customer ID failed
            error_message = f"Failed to get customer ID with status code: {response.status_code}"
            if response.text:
                error_message += f" - {response.text}"
            
            self.log_message(error_message)
            return False
            
        except Exception as e:
            self.log_message(f"Error getting customer ID: {str(e)}")
            return False
    
    def sign_out(self):
        """Sign out and revoke the auth token"""
        if not self.auth_token:
            return
        
        try:
            headers = {
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Auth-Token": self.auth_token
            }
            
            payload = {
                "access_token": self.auth_token
            }
            
            response = requests.post(
                f"https://{self.server}/auth/oauth2/revoke-token",
                headers=headers,
                data=payload,
                verify=False
            )
            
            if response.status_code == 200:
                self.log_message("Successfully signed out and revoked token")
            else:
                self.log_message(f"Sign out failed with status code: {response.status_code}")
            
        except Exception as e:
            self.log_message(f"Error during sign out: {str(e)}")
    
    def confirm_update(self):
        """Show confirmation dialog before updating emails"""
        # Add debug logging
        self.log_message("DEBUG: confirm_update method called")
        system_log_message("DEBUG: confirm_update method called")
        
        # Get count of users to update
        external_users = [user for user in self.sanitized_users if user.get("Classification") == "External"]
        if not external_users:
            QMessageBox.information(self, "No Users to Update", "No external users found to update.")
            self.log_message("DEBUG: No external users found to update")
            system_log_message("DEBUG: No external users found to update")
            return
        
        # Create a dialog with the list of users to update
        dialog = QDialog(self)
        dialog.setWindowTitle("Confirm Email Updates")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        dialog.setStyleSheet("background-color: white;")
        
        # ADDITIONAL DEBUG: Log that we're creating the dialog
        self.log_message("DEBUG: Creating confirmation dialog")
        system_log_message("DEBUG: Creating confirmation dialog")
        
        layout = QVBoxLayout(dialog)
        
        # Warning message
        warning = QLabel(f"You are about to update {len(external_users)} user email addresses.")
        warning.setStyleSheet("font-weight: 600; color: #B91C1C; font-size: 16px;")
        layout.addWidget(warning)
        
        # Description
        desc = QLabel("This action will update the email addresses for the following external users. Please confirm to continue.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #475569; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # User list in text edit
        user_list = QTextEdit()
        user_list.setReadOnly(True)
        user_list.setStyleSheet("""
            border: 1px solid #E2E8F0;
            border-radius: 4px;
            padding: 8px;
            font-family: monospace;
            font-size: 13px;
        """)
        
        # Format user list
        user_text = ""
        for user in external_users:
            user_id = user.get("UserID", "")
            name = user.get("FullName", "")
            old_email = user.get("Email", "")
            new_email = user.get("NewEmail", "")
            user_text += f"ID: {user_id}\nName: {name}\nFrom: {old_email}\nTo: {new_email}\n\n"
        
        user_list.setText(user_text)
        layout.addWidget(user_list)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No)
        button_box.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton[text="Yes"] {
                background-color: #DC2626;
                color: white;
                border: none;
            }
            QPushButton[text="Yes"]:hover {
                background-color: #B91C1C;
            }
            QPushButton[text="No"] {
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
            }
        """)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # ADDITIONAL DEBUG: Log that we're about to show the dialog
        self.log_message("DEBUG: About to show confirmation dialog - MAKE SURE TO CLICK YES")
        system_log_message("DEBUG: About to show confirmation dialog - MAKE SURE TO CLICK YES")
        
        # Show dialog and process result
        result = dialog.exec()
        self.log_message(f"DEBUG: User confirmation result: {result == QDialog.DialogCode.Accepted}")
        system_log_message(f"DEBUG: User confirmation result: {result == QDialog.DialogCode.Accepted}")
        
        # Force update to system_log file immediately to ensure we can see the debug messages
        try:
            # Force flush logs to disk
            import sys
            sys.stdout.flush()
            
            # Also manually write to system log for immediate visibility
            log_dir = Path(__file__).parent / "Logs"
            system_log_path = log_dir / "system_log.txt"
            with open(system_log_path, 'a', encoding='utf-8') as sys_log:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sys_log.write(f"{timestamp} - DEBUG: Confirmation dialog result: {result == QDialog.DialogCode.Accepted}\n")
        except Exception as e:
            print(f"Failed to force log flush: {str(e)}")
        
        if result == QDialog.DialogCode.Accepted:
            self.log_message("DEBUG: User confirmed update, calling update_emails()")
            system_log_message("DEBUG: User confirmed update, calling update_emails()")
            
            # BYPASS DIALOG FOR TESTING - Force update to run
            self.update_emails()
            # Uncomment the line above and comment the next line to force the update
            # self.update_emails()
        else:
            # ADDITIONAL DEBUG: Log when user selects "No"
            self.log_message("DEBUG: User declined the update - no emails will be updated")
            system_log_message("DEBUG: User declined the update - no emails will be updated")
    
    def update_emails(self):
        """Update the emails for external users"""
        external_users = [user for user in self.sanitized_users if user.get("Classification") == "External"]
        if not external_users:
            return

        # Show progress UI
        self.progress_container.setVisible(True)
        self.progress_bar.setRange(0, len(external_users))
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting email updates...")
        
        # Create a detailed status panel for showing live updates
        self.setup_status_panel()
        
        # Calculate initial ETA
        start_time = datetime.datetime.now()
        self.start_time = start_time
        estimated_time_per_user = 2.0  # Initial estimate: 2 seconds per user
        estimated_total_seconds = len(external_users) * estimated_time_per_user
        
        # Add pause time for every 10 users (rate limit)
        rate_limit_pauses = (len(external_users) - 1) // self.rate_limit
        estimated_total_seconds += rate_limit_pauses * self.pause_time
        
        estimated_completion_time = start_time + datetime.timedelta(seconds=estimated_total_seconds)
        formatted_eta = estimated_completion_time.strftime("%H:%M:%S")
        
        self.update_eta_label(formatted_eta, estimated_total_seconds)
        
        # Disable buttons during update
        self.update_btn.setEnabled(False)
        self.back_btn.setEnabled(False)
        QApplication.processEvents()
        
        # Start update operation
        self.log_message("Starting email update for users...")
        
        # Determine API base URL
        base_url = f"https://{self.server}/api/v2/customers/{self.customer_id}"
        if not self.server.lower().endswith("cloudimanage.com"):
            base_url = f"{base_url}/libraries/{self.library}"
        
        self.log_message(f"Using API base URL: {base_url}")
        system_log_message(f"IMANAGE API - Using API base URL: {base_url}")
        
        update_count = 0
        success_count = 0
        failed_count = 0
        
        # Create a list to store the recent log entries
        self.recent_logs = []
        
        try:
            for i, user in enumerate(external_users):
                user_id = user.get("UserID", "")
                new_email = user.get("NewEmail", "")
                old_email = user.get("Email", "")
                
                if user_id and new_email:
                    # Update progress
                    self.progress_bar.setValue(i)
                    progress_pct = int((i / len(external_users)) * 100)
                    self.progress_bar.setFormat(f"{progress_pct}% ({i}/{len(external_users)})")
                    
                    status_msg = f"Updating user {i+1} of {len(external_users)}: {user_id}"
                    self.progress_label.setText(status_msg)
                    self.add_to_live_log(status_msg)
                    QApplication.processEvents()
                    
                    try:
                        # Prepare payload
                        payload = {
                            "email": new_email
                        }
                        
                        # Add ID for cloud instances
                        if self.server.lower().endswith("cloudimanage.com"):
                            payload["id"] = user_id
                        
                        # Make API call
                        update_url = f"{base_url}/users/{user_id}"
                        
                        # Log the request details to both logs and console
                        request_log = f"IMANAGE API REQUEST: PATCH {update_url}"
                        self.log_message(request_log)
                        system_log_message(request_log)
                        
                        payload_log = f"IMANAGE API REQUEST PAYLOAD: {json.dumps(payload)}"
                        self.log_message(payload_log)
                        system_log_message(payload_log)
                        
                        # Send the request
                        response = requests.patch(
                            update_url,
                            headers=self.headers,
                            json=payload,
                            verify=False
                        )
                        
                        # Log the response details to both logs and console
                        response_log = f"IMANAGE API RESPONSE STATUS: {response.status_code}"
                        self.log_message(response_log)
                        system_log_message(response_log)
                        
                        try:
                            resp_json = response.json()
                            resp_body_log = f"IMANAGE API RESPONSE BODY: {json.dumps(resp_json)}"
                            self.log_message(resp_body_log)
                            system_log_message(resp_body_log)
                        except:
                            resp_body_log = f"IMANAGE API RESPONSE BODY: {response.text}"
                            self.log_message(resp_body_log)
                            system_log_message(resp_body_log)
                        
                        # Process response
                        if response.status_code in [200, 201, 204]:
                            success_message = f"✅ User update successful: {user_id} - Email changed from '{old_email}' to '{new_email}'"
                            self.log_message(success_message)
                            system_log_message(success_message)
                            self.add_to_live_log(success_message)
                            success_count += 1
                        else:
                            error_message = f"❌ User update failed: {user_id} - Status: {response.status_code}"
                            if response.text:
                                error_message += f" - {response.text}"
                            self.log_message(error_message)
                            system_log_message(error_message)
                            self.add_to_live_log(error_message)
                            failed_count += 1
                        
                        # Rate limiting - pause to avoid overwhelming server
                        update_count += 1
                        if update_count % self.rate_limit == 0 and i < len(external_users) - 1:
                            # Instead of a dialog, update the UI directly
                            self.handle_rate_limit_pause(self.pause_time, i, len(external_users))
                            
                            # Recalculate ETA after the pause
                            current_time = datetime.datetime.now()
                            elapsed_seconds = (current_time - start_time).total_seconds()
                            processed_users = i + 1
                            
                            if processed_users > 0:
                                seconds_per_user = elapsed_seconds / processed_users
                                remaining_users = len(external_users) - processed_users
                                remaining_pauses = remaining_users // self.rate_limit
                                
                                estimated_remaining_seconds = (remaining_users * seconds_per_user) + (remaining_pauses * self.pause_time)
                                new_eta = current_time + datetime.timedelta(seconds=estimated_remaining_seconds)
                                formatted_eta = new_eta.strftime("%H:%M:%S")
                                
                                self.update_eta_label(formatted_eta, estimated_remaining_seconds)
                            
                    except Exception as e:
                        error_message = f"Error updating user {user_id}: {str(e)}"
                        self.log_message(error_message)
                        system_log_message(error_message)
                        self.add_to_live_log(f"❌ {error_message}")
                        
                        # Log exception details
                        import traceback
                        trace_message = f"EXCEPTION DETAILS: {traceback.format_exc()}"
                        self.log_message(trace_message)
                        system_log_message(trace_message)
                        
                        failed_count += 1
            
            # Final progress update
            self.progress_bar.setValue(len(external_users))
            result_message = f"Update completed: {success_count} succeeded, {failed_count} failed"
            self.progress_label.setText(result_message)
            self.add_to_live_log(f"✅ {result_message}")
            self.log_message("Email update process completed for all users.")
            system_log_message("Email update process completed for all users.")
            
            # Calculate and show final statistics
            end_time = datetime.datetime.now()
            duration = end_time - start_time
            duration_str = str(duration).split('.')[0]  # Remove microseconds
            
            stats_message = (
                f"Total time: {duration_str}\n"
                f"Total users processed: {len(external_users)}\n"
                f"Success rate: {success_count/len(external_users)*100:.1f}%"
            )
            self.add_to_live_log(stats_message)
            
            # Show results message
            QMessageBox.information(self, "Update Complete", result_message)
            
        except Exception as e:
            error_message = f"Error during email update: {str(e)}"
            self.log_message(error_message)
            system_log_message(error_message)
            self.add_to_live_log(f"❌ {error_message}")
            QMessageBox.critical(self, "Update Error", f"An error occurred: {str(e)}")
        finally:
            # Clean up
            self.sign_out()
            
            # Re-enable buttons
            self.update_btn.setEnabled(True)
            self.back_btn.setEnabled(True)
            self.status_label.setText("Email update completed")
    
    def setup_status_panel(self):
        """Create a status panel to show detailed progress"""
        # If a status panel already exists, remove it
        if hasattr(self, 'status_panel'):
            # Check if the status panel is already in the layout
            try:
                if self.status_panel.parent():
                    self.status_panel.parent().layout().removeWidget(self.status_panel)
                    self.status_panel.deleteLater()
            except Exception:
                pass
        
        # Create status panel
        self.status_panel = QFrame()
        self.status_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.status_panel.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
        """)
        
        status_layout = QVBoxLayout(self.status_panel)
        status_layout.setContentsMargins(16, 16, 16, 16)
        status_layout.setSpacing(12)
        
        # Status title
        status_title = QLabel("Email Update Status")
        status_title.setStyleSheet("""
            font-weight: 600;
            font-size: 16px;
            color: #334155;
        """)
        status_layout.addWidget(status_title)
        
        # Live progress section
        progress_section = QWidget()
        progress_section_layout = QHBoxLayout(progress_section)
        progress_section_layout.setContentsMargins(0, 0, 0, 0)
        progress_section_layout.setSpacing(20)
        
        # Left column for counters
        counters_widget = QWidget()
        counters_layout = QVBoxLayout(counters_widget)
        counters_layout.setContentsMargins(0, 0, 0, 0)
        counters_layout.setSpacing(8)
        
        # ETA
        eta_container = QWidget()
        eta_layout = QHBoxLayout(eta_container)
        eta_layout.setContentsMargins(0, 0, 0, 0)
        eta_layout.setSpacing(8)
        
        eta_label = QLabel("Estimated completion:")
        eta_label.setStyleSheet("color: #64748B; font-size: 14px;")
        
        self.eta_value = QLabel("Calculating...")
        self.eta_value.setStyleSheet("color: #334155; font-weight: 500; font-size: 14px;")
        
        eta_layout.addWidget(eta_label)
        eta_layout.addWidget(self.eta_value)
        eta_layout.addStretch()
        
        counters_layout.addWidget(eta_container)
        
        # Progress section for both overall and rate limit progress
        self.overall_progress_section = QWidget()
        overall_progress_layout = QVBoxLayout(self.overall_progress_section)
        overall_progress_layout.setContentsMargins(0, 0, 0, 0)
        overall_progress_layout.setSpacing(4)
        
        overall_progress_label = QLabel("Overall Progress:")
        overall_progress_label.setStyleSheet("color: #64748B; font-size: 14px;")
        overall_progress_layout.addWidget(overall_progress_label)
        
        # We'll use the existing progress bar
        counters_layout.addWidget(self.overall_progress_section)
        
        # Rate limit progress (only shown during rate limiting)
        self.rate_limit_section = QWidget()
        rate_limit_layout = QVBoxLayout(self.rate_limit_section)
        rate_limit_layout.setContentsMargins(0, 0, 0, 0)
        rate_limit_layout.setSpacing(4)
        
        self.rate_limit_label = QLabel("API Rate Limiting Pause:")
        self.rate_limit_label.setStyleSheet("color: #64748B; font-size: 14px;")
        rate_limit_layout.addWidget(self.rate_limit_label)
        
        self.rate_limit_progress = QProgressBar()
        self.rate_limit_progress.setRange(0, 100)
        self.rate_limit_progress.setValue(0)
        self.rate_limit_progress.setFormat("%v seconds remaining")
        self.rate_limit_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                background-color: #F1F5F9;
                text-align: center;
                padding: 2px;
                height: 12px;
                color: #334155;
            }
            QProgressBar::chunk {
                background-color: #DBEAFE;
                border-radius: 3px;
            }
        """)
        rate_limit_layout.addWidget(self.rate_limit_progress)
        
        self.rate_limit_description = QLabel(
            "To prevent overwhelming the server, we need to pause briefly between batches of updates."
        )
        self.rate_limit_description.setWordWrap(True)
        self.rate_limit_description.setStyleSheet("color: #64748B; font-size: 12px; font-style: italic;")
        rate_limit_layout.addWidget(self.rate_limit_description)
        
        counters_layout.addWidget(self.rate_limit_section)
        self.rate_limit_section.hide()  # Initially hidden
        
        # Right column for live log
        self.live_log = QTextEdit()
        self.live_log.setReadOnly(True)
        self.live_log.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
                font-size: 12px;
                color: #334155;
            }
        """)
        self.live_log.setFixedHeight(200)  # Limit height
        
        # Add both columns to the progress section
        progress_section_layout.addWidget(counters_widget, 1)  # 40% width
        progress_section_layout.addWidget(self.live_log, 2)    # 60% width
        
        status_layout.addWidget(progress_section)
        
        # Find a suitable place to insert the status panel in the main layout
        content_layout = None
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item.widget() and isinstance(item.widget(), QFrame):
                # Found the main content panel
                content_panel = item.widget()
                content_layout = content_panel.layout()
                break
        
        if content_layout:
            # Insert status panel before the action buttons but after the progress bar
            for i in range(content_layout.count()):
                item = content_layout.itemAt(i)
                if item and item.widget() == self.progress_container:
                    content_layout.insertWidget(i+1, self.status_panel)
                    break
    
    def update_eta_label(self, formatted_time, seconds_remaining):
        """Update the ETA label with the estimated completion time"""
        remaining_time = datetime.timedelta(seconds=int(seconds_remaining))
        
        # Format as HH:MM:SS for display
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        remaining_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        self.eta_value.setText(f"~{formatted_time} ({remaining_str} remaining)")
    
    def add_to_live_log(self, message):
        """Add a message to the live log display"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        full_message = f"[{timestamp}] {message}"
        
        # Keep only the most recent messages (limit to 100 for performance)
        self.recent_logs.append(full_message)
        if len(self.recent_logs) > 100:
            self.recent_logs.pop(0)
        
        # Update the text edit with all recent logs
        self.live_log.setPlainText('\n'.join(self.recent_logs))
        
        # Scroll to bottom
        self.live_log.verticalScrollBar().setValue(
            self.live_log.verticalScrollBar().maximum()
        )
        
        # Process UI events to keep the interface responsive
        QApplication.processEvents()
    
    def handle_rate_limit_pause(self, pause_seconds, current_user, total_users):
        """Handle the rate limit pause within the main UI"""
        pause_message = f"Pausing for {pause_seconds} seconds to avoid API rate limiting..."
        self.log_message(pause_message)
        system_log_message(pause_message)
        self.add_to_live_log(f"⏱️ {pause_message}")
        
        # Show rate limit section
        self.rate_limit_section.show()
        self.rate_limit_progress.setRange(0, pause_seconds)
        
        # Update the main progress indicator
        overall_progress = int(((current_user + 1) / total_users) * 100)
        self.progress_bar.setValue(current_user + 1)
        self.progress_bar.setFormat(f"{overall_progress}% ({current_user + 1}/{total_users})")
        
        # Update the progress label
        self.progress_label.setText(f"API rate limit reached. Pausing before continuing...")
        QApplication.processEvents()
        
        # Handle the countdown
        for remaining in range(pause_seconds, 0, -1):
            self.rate_limit_progress.setValue(pause_seconds - remaining)
            self.rate_limit_progress.setFormat(f"{remaining} seconds remaining")
            
            # Update rate limit message in the main progress area
            if remaining > 1:
                self.progress_label.setText(f"API rate limit reached. Resuming in {remaining} seconds...")
            else:
                self.progress_label.setText(f"API rate limit reached. Resuming in 1 second...")
                
            QApplication.processEvents()
            time.sleep(1)
        
        # Final update
        self.rate_limit_progress.setValue(pause_seconds)
        self.rate_limit_progress.setFormat("Resuming...")
        self.progress_label.setText("Resuming email updates...")
        QApplication.processEvents()
        
        # Hide rate limit section after pause completes
        self.rate_limit_section.hide()
        
        # Log the resumption
        resume_message = "Rate limit pause completed, resuming updates..."
        self.log_message(resume_message)
        system_log_message(resume_message)
        self.add_to_live_log(f"▶️ {resume_message}")
    
    def log_message(self, message):
        """Write a message to the log file and system log"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp} - {message}"
            
            with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"{log_entry}\n")
                
            # Also log to the main system log for the overlay to pick up
            system_log_message(f"[EMAIL UPDATER] {message}")
            
            # Always print API requests to the consolidated log
            if "REQUEST:" in message or "RESPONSE:" in message:
                # Write to consolidated log file
                consolidated_log_path = self.log_dir / "consolidated_log.txt"
                with open(consolidated_log_path, 'a', encoding='utf-8') as consolidated_log:
                    consolidated_log.write(f"{log_entry}\n")
            
            print(log_entry)  # Also print to console for debugging
            
        except Exception as e:
            print(f"Error writing to log: {str(e)}")
    
    def set_sanitized_users(self, users):
        """Set the sanitized users data and update the table"""
        self.sanitized_users = users
        self.populate_users_table()
    
    def closeEvent(self, event):
        """Clean up resources when closing the widget"""
        # Sign out if token exists
        if self.auth_token:
            self.sign_out()
        
        super().closeEvent(event)


def update_emails(sanitized_users):
    """Main function to update emails for sanitized users"""
    from ui.utils import log_function_execution, log_message
    import json
    from pathlib import Path
    import requests
    import urllib3
    import time
    import datetime
    
    # Disable SSL warnings for older server compatibility
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        # Log start of email update process
        log_function_execution("email_updater", "START", {
            "users_count": len(sanitized_users)
        })
        
        # Count external users to update
        external_users = [user for user in sanitized_users if user.get("Classification") == "External"]
        update_count = len(external_users)
        
        if update_count == 0:
            log_message("No external users found to update emails")
            log_function_execution("email_updater", "COMPLETE", {
                "updated_count": 0,
                "message": "No emails to update"
            })
            return sanitized_users
        
        # Load server configuration from settings
        config_path = Path(__file__).parent.parent / "config" / "login_settings.json"
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Support both lowercase and uppercase first letter keys for compatibility
                server = config.get("Server", "") or config.get("server", "")
                username = config.get("Username", "") or config.get("username", "")
                password = config.get("Password", "") or config.get("password", "")
                client_id = config.get("Client ID", "") or config.get("client_id", "")
                client_secret = config.get("Client Secret", "") or config.get("client_secret", "")
                library = config.get("Library ID", "") or config.get("library", "")
                customer_id = config.get("Customer ID", "") or config.get("customer_id", "")
                
                # Log the config values we're using (masking sensitive values)
                log_message(f"Using server: {server}")
                log_message(f"Using library: {library}")
                log_message(f"Using customer ID: {customer_id}")
                log_message(f"Username provided: {'Yes' if username else 'No'}")
                log_message(f"Password provided: {'Yes' if password else 'No'}")
                log_message(f"Client ID provided: {'Yes' if client_id else 'No'}")
                log_message(f"Client Secret provided: {'Yes' if client_secret else 'No'}")
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            error_msg = f"Failed to load server configuration: {str(e)}"
            log_message(error_msg)
            log_function_execution("email_updater", "FAILED", {
                "error": error_msg
            })
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Configuration Error", 
                             "Failed to load server configuration. Please check your settings.")
            return sanitized_users
            
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / "updatescriptlog.txt"
        
        # Log message function
        def log_to_file(message):
            try:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_entry = f"{timestamp} - {message}"
                
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"{log_entry}\n")
                    
                # Also log to system log
                log_message(f"[EMAIL UPDATER] {message}")
                
                # Log to consolidated log if it's an API request/response
                if "REQUEST:" in message or "RESPONSE:" in message:
                    consolidated_log_path = log_dir / "consolidated_log.txt"
                    with open(consolidated_log_path, 'a', encoding='utf-8') as consolidated_log:
                        consolidated_log.write(f"{log_entry}\n")
                
                print(log_entry)  # For debugging
                
            except Exception as e:
                print(f"Error writing to log: {str(e)}")
        
        # Sign in to get authentication token
        log_to_file("Attempting to sign in to iManage server...")
        
        if not server:
            log_to_file("Server hostname not configured")
            log_function_execution("email_updater", "FAILED", {
                "error": "Server hostname not configured"
            })
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Configuration Error", 
                             "Server hostname not configured. Please check your settings.")
            return sanitized_users
        
        # Authentication headers
        auth_headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Create OAuth2 payload for authentication
        auth_payload = {
            "username": username,
            "password": password,
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "admin"
        }
        
        # Send authentication request
        try:
            auth_response = requests.post(
                f"https://{server}/auth/oauth2/token",
                headers=auth_headers,
                data=auth_payload,
                verify=False  # Disable SSL verification
            )
            
            # Log the authentication response
            log_to_file(f"Authentication response status: {auth_response.status_code}")
            
            if auth_response.status_code != 200:
                error_msg = f"Authentication failed: {auth_response.text}"
                log_to_file(error_msg)
                log_function_execution("email_updater", "FAILED", {
                    "error": error_msg
                })
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Authentication Error", 
                                 "Failed to authenticate with the iManage server. Please check your credentials.")
                return sanitized_users
                
            # Extract auth token
            auth_data = auth_response.json()
            auth_token = auth_data.get("access_token")
            
            if not auth_token:
                log_to_file("Failed to retrieve authentication token")
                log_function_execution("email_updater", "FAILED", {
                    "error": "No authentication token in response"
                })
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Authentication Error", 
                                 "Failed to retrieve authentication token.")
                return sanitized_users
                
            log_to_file("Successfully authenticated with iManage server")
            
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            log_to_file(error_msg)
            log_function_execution("email_updater", "FAILED", {
                "error": error_msg
            })
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Authentication Error", 
                             f"Error connecting to server: {str(e)}")
            return sanitized_users
        
        # Set up headers for API calls
        api_headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "X-Auth-Token": auth_token
        }
        
        # Get customer ID
        try:
            customer_response = requests.get(
                f"https://{server}/api",
                headers=api_headers,
                verify=False
            )
            
            if customer_response.status_code != 200:
                error_msg = f"Failed to get customer ID: {customer_response.text}"
                log_to_file(error_msg)
                log_function_execution("email_updater", "FAILED", {
                    "error": error_msg
                })
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "API Error", 
                                 "Failed to retrieve customer information.")
                return sanitized_users
            
            customer_data = customer_response.json()
            customer_id = customer_data.get("data", {}).get("user", {}).get("customer_id")
            
            if not customer_id:
                log_to_file("Failed to extract customer ID from response")
                log_function_execution("email_updater", "FAILED", {
                    "error": "No customer ID in response"
                })
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "API Error", 
                                 "Failed to extract customer ID from response.")
                return sanitized_users
                
            log_to_file(f"Successfully retrieved customer ID: {customer_id}")
            
        except Exception as e:
            error_msg = f"Error getting customer ID: {str(e)}"
            log_to_file(error_msg)
            log_function_execution("email_updater", "FAILED", {
                "error": error_msg
            })
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "API Error", 
                             f"Error retrieving customer information: {str(e)}")
            return sanitized_users
        
        # Set up base URL for API calls
        base_url = f"https://{server}/api/v2/customers/{customer_id}"
        if not server.lower().endswith("cloudimanage.com") and library:
            base_url = f"{base_url}/libraries/{library}"
        
        log_to_file(f"Using API base URL: {base_url}")
        
        # API rate limiting settings
        pause_time = 60  # seconds
        rate_limit = 10  # API calls before pausing
        api_count = 0
        success_count = 0
        failed_count = 0
        
        # Calculate initial ETA
        start_time = datetime.datetime.now()
        estimated_time_per_user = 2.0  # Initial estimate: 2 seconds per user
        estimated_total_seconds = len(external_users) * estimated_time_per_user
        
        # Add pause time for every 10 users (rate limit)
        rate_limit_pauses = (len(external_users) - 1) // rate_limit
        estimated_total_seconds += rate_limit_pauses * pause_time
        
        estimated_completion_time = start_time + datetime.timedelta(seconds=estimated_total_seconds)
        formatted_eta = estimated_completion_time.strftime("%H:%M:%S")
        
        # Log the start of the update process with ETA
        log_to_file(f"Starting email updates for {len(external_users)} external users. Estimated completion: {formatted_eta}")
        
        # Try to create a progress indicator if we're in a UI environment
        progress_widget = None
        try:
            from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout, QFrame
            from PyQt6.QtCore import Qt, QTimer
            
            # Check if QApplication instance exists
            if QApplication.instance():
                progress_dialog = QDialog(None)
                progress_dialog.setWindowTitle("Updating Emails")
                progress_dialog.setFixedSize(600, 400)
                progress_dialog.setStyleSheet("""
                    QDialog {
                        background-color: white;
                        border-radius: 8px;
                    }
                """)
                
                # Make it non-modal but stay on top
                progress_dialog.setWindowFlags(
                    Qt.WindowType.Dialog | 
                    Qt.WindowType.WindowStaysOnTopHint
                )
                
                # Main layout
                main_layout = QVBoxLayout(progress_dialog)
                main_layout.setContentsMargins(20, 20, 20, 20)
                main_layout.setSpacing(15)
                
                # Title
                title = QLabel("Email Update Progress")
                title.setStyleSheet("""
                    font-size: 18px;
                    font-weight: 600;
                    color: #1E293B;
                """)
                main_layout.addWidget(title)
                
                # Status section with counters
                status_frame = QFrame()
                status_frame.setStyleSheet("""
                    background-color: #F8FAFC;
                    border-radius: 8px;
                    border: 1px solid #E2E8F0;
                    padding: 10px;
                """)
                status_layout = QHBoxLayout(status_frame)
                
                # Left side - counters
                counters_widget = QWidget()
                counters_layout = QVBoxLayout(counters_widget)
                counters_layout.setContentsMargins(0, 0, 0, 0)
                counters_layout.setSpacing(10)
                
                # ETA
                eta_widget = QWidget()
                eta_layout = QHBoxLayout(eta_widget)
                eta_layout.setContentsMargins(0, 0, 0, 0)
                
                eta_label = QLabel("Estimated Completion:")
                eta_label.setStyleSheet("color: #64748B; font-weight: 500;")
                
                eta_value = QLabel(formatted_eta)
                eta_value.setStyleSheet("color: #0F172A; font-weight: 600;")
                
                eta_layout.addWidget(eta_label)
                eta_layout.addWidget(eta_value)
                eta_layout.addStretch()
                
                counters_layout.addWidget(eta_widget)
                
                # Progress metrics
                progress_metrics = QWidget()
                metrics_layout = QHBoxLayout(progress_metrics)
                metrics_layout.setContentsMargins(0, 0, 0, 0)
                metrics_layout.setSpacing(20)
                
                # Processed count
                processed_widget = QWidget()
                processed_layout = QVBoxLayout(processed_widget)
                processed_layout.setContentsMargins(0, 0, 0, 0)
                processed_layout.setSpacing(2)
                
                processed_label = QLabel("Processed")
                processed_label.setStyleSheet("color: #64748B; font-size: 12px;")
                
                processed_count = QLabel("0")
                processed_count.setStyleSheet("color: #0F172A; font-size: 24px; font-weight: 600;")
                processed_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                processed_layout.addWidget(processed_label, alignment=Qt.AlignmentFlag.AlignCenter)
                processed_layout.addWidget(processed_count, alignment=Qt.AlignmentFlag.AlignCenter)
                
                # Success count
                success_widget = QWidget()
                success_layout = QVBoxLayout(success_widget)
                success_layout.setContentsMargins(0, 0, 0, 0)
                success_layout.setSpacing(2)
                
                success_label = QLabel("Successful")
                success_label.setStyleSheet("color: #64748B; font-size: 12px;")
                
                success_count_label = QLabel("0")
                success_count_label.setStyleSheet("color: #059669; font-size: 24px; font-weight: 600;")
                success_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                success_layout.addWidget(success_label, alignment=Qt.AlignmentFlag.AlignCenter)
                success_layout.addWidget(success_count_label, alignment=Qt.AlignmentFlag.AlignCenter)
                
                # Failed count
                failed_widget = QWidget()
                failed_layout = QVBoxLayout(failed_widget)
                failed_layout.setContentsMargins(0, 0, 0, 0)
                failed_layout.setSpacing(2)
                
                failed_label = QLabel("Failed")
                failed_label.setStyleSheet("color: #64748B; font-size: 12px;")
                
                failed_count_label = QLabel("0")
                failed_count_label.setStyleSheet("color: #DC2626; font-size: 24px; font-weight: 600;")
                failed_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                failed_layout.addWidget(failed_label, alignment=Qt.AlignmentFlag.AlignCenter)
                failed_layout.addWidget(failed_count_label, alignment=Qt.AlignmentFlag.AlignCenter)
                
                # Remaining count
                remaining_widget = QWidget()
                remaining_layout = QVBoxLayout(remaining_widget)
                remaining_layout.setContentsMargins(0, 0, 0, 0)
                remaining_layout.setSpacing(2)
                
                remaining_label = QLabel("Remaining")
                remaining_label.setStyleSheet("color: #64748B; font-size: 12px;")
                
                remaining_count = QLabel(str(len(external_users)))
                remaining_count.setStyleSheet("color: #0F172A; font-size: 24px; font-weight: 600;")
                remaining_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                remaining_layout.addWidget(remaining_label, alignment=Qt.AlignmentFlag.AlignCenter)
                remaining_layout.addWidget(remaining_count, alignment=Qt.AlignmentFlag.AlignCenter)
                
                # Add all metrics to layout
                metrics_layout.addWidget(processed_widget)
                metrics_layout.addWidget(success_widget)
                metrics_layout.addWidget(failed_widget)
                metrics_layout.addWidget(remaining_widget)
                
                counters_layout.addWidget(progress_metrics)
                
                # Overall progress
                progress_section = QWidget()
                progress_section_layout = QVBoxLayout(progress_section)
                progress_section_layout.setContentsMargins(0, 0, 0, 0)
                progress_section_layout.setSpacing(5)
                
                progress_label = QLabel("Overall Progress:")
                progress_label.setStyleSheet("color: #64748B;")
                
                progress_bar = QProgressBar()
                progress_bar.setRange(0, len(external_users))
                progress_bar.setValue(0)
                progress_bar.setFormat("%v/%m (%p%)")
                progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #E2E8F0;
                        border-radius: 4px;
                        background-color: #F1F5F9;
                        text-align: center;
                        padding: 2px;
                        height: 16px;
                        color: #334155;
                    }
                    QProgressBar::chunk {
                        background-color: #3B82F6;
                        border-radius: 3px;
                    }
                """)
                
                progress_section_layout.addWidget(progress_label)
                progress_section_layout.addWidget(progress_bar)
                
                counters_layout.addWidget(progress_section)
                
                # Rate limit section (hidden initially)
                rate_limit_section = QWidget()
                rate_limit_layout = QVBoxLayout(rate_limit_section)
                rate_limit_layout.setContentsMargins(0, 0, 0, 0)
                rate_limit_layout.setSpacing(5)
                
                rate_limit_label = QLabel("API Rate Limit Pause:")
                rate_limit_label.setStyleSheet("color: #64748B;")
                
                rate_limit_progress = QProgressBar()
                rate_limit_progress.setRange(0, pause_time)
                rate_limit_progress.setValue(0)
                rate_limit_progress.setFormat("%v seconds remaining")
                rate_limit_progress.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #E2E8F0;
                        border-radius: 4px;
                        background-color: #F1F5F9;
                        text-align: center;
                        padding: 2px;
                        height: 16px;
                        color: #334155;
                    }
                    QProgressBar::chunk {
                        background-color: #DBEAFE;
                        border-radius: 3px;
                    }
                """)
                
                rate_limit_layout.addWidget(rate_limit_label)
                rate_limit_layout.addWidget(rate_limit_progress)
                
                rate_limit_info = QLabel("To prevent overwhelming the server, we pause after every 10 users.")
                rate_limit_info.setStyleSheet("color: #64748B; font-style: italic; font-size: 12px;")
                rate_limit_info.setWordWrap(True)
                
                rate_limit_layout.addWidget(rate_limit_info)
                
                counters_layout.addWidget(rate_limit_section)
                rate_limit_section.hide()  # Hide initially
                
                status_layout.addWidget(counters_widget)
                
                main_layout.addWidget(status_frame)
                
                # Current operation
                current_op_label = QLabel("Starting email updates...")
                current_op_label.setStyleSheet("color: #334155; font-size: 14px;")
                main_layout.addWidget(current_op_label)
                
                # Log area
                log_label = QLabel("Log:")
                log_label.setStyleSheet("color: #64748B; font-weight: 500;")
                main_layout.addWidget(log_label)
                
                from PyQt6.QtWidgets import QTextEdit
                log_area = QTextEdit()
                log_area.setReadOnly(True)
                log_area.setStyleSheet("""
                    QTextEdit {
                        border: 1px solid #E2E8F0;
                        border-radius: 4px;
                        background-color: #F8FAFC;
                        padding: 8px;
                        font-family: monospace;
                        font-size: 12px;
                        color: #334155;
                    }
                """)
                log_area.setFixedHeight(150)
                main_layout.addWidget(log_area)
                
                # Show dialog
                progress_dialog.show()
                QApplication.processEvents()
                
                # Store references to controls for updating
                progress_widget = {
                    'dialog': progress_dialog,
                    'eta_value': eta_value,
                    'processed_count': processed_count,
                    'success_count': success_count_label,
                    'failed_count': failed_count_label,
                    'remaining_count': remaining_count,
                    'progress_bar': progress_bar,
                    'current_op': current_op_label,
                    'log_area': log_area,
                    'rate_limit_section': rate_limit_section,
                    'rate_limit_progress': rate_limit_progress,
                    'logs': []  # Store recent logs
                }
                
        except Exception as e:
            log_to_file(f"Note: Unable to create progress UI: {str(e)}")
            progress_widget = None
        
        # Custom logging function that updates UI if available
        def log_with_ui(message, is_error=False, is_success=False):
            # Standard logging
            log_to_file(message)
            
            # Update UI if available
            if progress_widget:
                try:
                    # Add message to logs
                    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                    
                    # Format message with emoji based on type
                    if is_error:
                        formatted_message = f"❌ {message}"
                    elif is_success:
                        formatted_message = f"✅ {message}"
                    else:
                        formatted_message = message
                    
                    log_entry = f"[{timestamp}] {formatted_message}"
                    progress_widget['logs'].append(log_entry)
                    
                    # Keep only latest 100 logs
                    if len(progress_widget['logs']) > 100:
                        progress_widget['logs'] = progress_widget['logs'][-100:]
                    
                    # Update log display
                    progress_widget['log_area'].setPlainText('\n'.join(progress_widget['logs']))
                    
                    # Scroll to bottom
                    progress_widget['log_area'].verticalScrollBar().setValue(
                        progress_widget['log_area'].verticalScrollBar().maximum()
                    )
                    
                    # Process events to keep UI responsive
                    QApplication.processEvents()
                    
                except Exception as e:
                    # Just log the error but continue with standard logging
                    print(f"Error updating UI log: {str(e)}")
        
        # Process each external user
        log_with_ui(f"Starting email updates for {len(external_users)} external users")
        
        for i, user in enumerate(external_users):
            user_id = user.get("UserID", "")
            old_email = user.get("Email", "")
            new_email = user.get("NewEmail", "")
            
            # Update progress UI
            if progress_widget:
                try:
                    progress_widget['processed_count'].setText(str(i))
                    progress_widget['remaining_count'].setText(str(len(external_users) - i))
                    progress_widget['progress_bar'].setValue(i)
                    progress_widget['current_op'].setText(f"Processing user {i+1} of {len(external_users)}: {user_id}")
                    QApplication.processEvents()
                except Exception:
                    pass  # Continue even if UI update fails
            
            # Debug info for each user
            log_with_ui(f"Processing user {i+1}/{len(external_users)}: {user_id}")
            log_with_ui(f"Email: {old_email} -> {new_email}")
            
            # Skip users missing critical information
            if not user_id:
                log_with_ui(f"Skipping user - missing UserID", is_error=True)
                continue
                
            if not new_email:
                log_with_ui(f"Skipping user {user_id} - missing New Email", is_error=True)
                continue
                
            # Skip if new email is the same as old email
            if new_email == old_email:
                log_with_ui(f"Skipping user {user_id} - new email is same as old email")
                continue
            
            # Prepare payload for update request
            payload = {
                "email": new_email,
                "id": user_id  # Always include the ID in the payload
            }
            
            update_url = f"{base_url}/users/{user_id}"
            
            # Log the request
            log_with_ui(f"IMANAGE API REQUEST: PATCH {update_url}")
            log_with_ui(f"IMANAGE API REQUEST PAYLOAD: {json.dumps(payload)}")
            
            try:
                # Send the update request
                response = requests.patch(
                    update_url,
                    headers=api_headers,
                    json=payload,
                    verify=False
                )
                
                # Log the response
                log_with_ui(f"IMANAGE API RESPONSE STATUS: {response.status_code}")
                
                try:
                    resp_json = response.json()
                    log_with_ui(f"IMANAGE API RESPONSE BODY: {json.dumps(resp_json)}")
                except:
                    log_with_ui(f"IMANAGE API RESPONSE BODY: {response.text}")
                
                # Process response
                if response.status_code in [200, 201, 204]:
                    success_message = f"User update successful: {user_id} - Email changed from '{old_email}' to '{new_email}'"
                    log_with_ui(success_message, is_success=True)
                    
                    # Update the email in our records
                    user["Email"] = new_email
                    success_count += 1
                    
                    # Update success count in UI
                    if progress_widget:
                        try:
                            progress_widget['success_count'].setText(str(success_count))
                            QApplication.processEvents()
                        except Exception:
                            pass
                            
                else:
                    error_message = f"User update failed: {user_id} - Status: {response.status_code}"
                    if response.text:
                        error_message += f" - {response.text}"
                    log_with_ui(error_message, is_error=True)
                    failed_count += 1
                    
                    # Update failed count in UI
                    if progress_widget:
                        try:
                            progress_widget['failed_count'].setText(str(failed_count))
                            QApplication.processEvents()
                        except Exception:
                            pass
                
                # Rate limiting - pause to avoid overwhelming server
                api_count += 1
                
                if api_count % rate_limit == 0 and i < len(external_users) - 1:
                    pause_message = f"Pausing for {pause_time} seconds to avoid API rate limiting..."
                    log_with_ui(f"⏱️ {pause_message}")
                    
                    # Update UI to show rate limiting
                    if progress_widget:
                        try:
                            progress_widget['current_op'].setText("API rate limit reached. Pausing before continuing...")
                            progress_widget['rate_limit_section'].show()
                            progress_widget['rate_limit_progress'].setRange(0, pause_time)
                            QApplication.processEvents()
                            
                            # Count down the pause time
                            for remaining in range(pause_time, 0, -1):
                                progress_widget['rate_limit_progress'].setValue(pause_time - remaining)
                                progress_widget['rate_limit_progress'].setFormat(f"{remaining} seconds remaining")
                                
                                # Update main status
                                progress_widget['current_op'].setText(f"API rate limit reached. Resuming in {remaining} seconds...")
                                
                                # Keep UI responsive during pause
                                QApplication.processEvents()
                                time.sleep(1)
                            
                            # Done with pause
                            progress_widget['rate_limit_progress'].setValue(pause_time)
                            progress_widget['rate_limit_progress'].setFormat("Resuming...")
                            progress_widget['current_op'].setText("Resuming email updates...")
                            QApplication.processEvents()
                            
                            # Hide rate limit section when done
                            progress_widget['rate_limit_section'].hide()
                            
                        except Exception as e:
                            # If UI update fails, just sleep
                            print(f"Error updating rate limit UI: {str(e)}")
                            time.sleep(pause_time)
                    else:
                        # No UI, just sleep
                        time.sleep(pause_time)
                    
                    # Recalculate ETA after each pause
                    current_time = datetime.datetime.now()
                    elapsed_seconds = (current_time - start_time).total_seconds()
                    
                    if i > 0:  # Only recalculate if we've processed at least one user
                        # Calculate actual time per user based on elapsed time
                        seconds_per_user = elapsed_seconds / (i + 1)
                        remaining_users = len(external_users) - (i + 1)
                        
                        # Estimate remaining pauses
                        remaining_pauses = remaining_users // rate_limit
                        
                        # Calculate remaining time
                        estimated_remaining_seconds = (remaining_users * seconds_per_user) + (remaining_pauses * pause_time)
                        new_eta = current_time + datetime.timedelta(seconds=estimated_remaining_seconds)
                        formatted_eta = new_eta.strftime("%H:%M:%S")
                        
                        # Log updated ETA
                        log_with_ui(f"Updated ETA: {formatted_eta}")
                        
                        # Update UI
                        if progress_widget:
                            try:
                                progress_widget['eta_value'].setText(formatted_eta)
                                QApplication.processEvents()
                            except Exception:
                                pass
                    
                    log_with_ui("Rate limit pause completed, resuming updates...")
                
            except Exception as e:
                error_message = f"Error updating user {user_id}: {str(e)}"
                log_with_ui(error_message, is_error=True)
                
                # Log exception details
                import traceback
                trace_message = f"EXCEPTION DETAILS: {traceback.format_exc()}"
                log_with_ui(trace_message)
                
                failed_count += 1
                
                # Update failed count in UI
                if progress_widget:
                    try:
                        progress_widget['failed_count'].setText(str(failed_count))
                        QApplication.processEvents()
                    except Exception:
                        pass
        
        # Final progress update
        if progress_widget:
            try:
                progress_widget['processed_count'].setText(str(len(external_users)))
                progress_widget['remaining_count'].setText("0")
                progress_widget['progress_bar'].setValue(len(external_users))
                QApplication.processEvents()
            except Exception:
                pass
        
        # Sign out / revoke token
        try:
            revoke_headers = {
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Auth-Token": auth_token
            }
            
            revoke_payload = {
                "access_token": auth_token
            }
            
            revoke_response = requests.post(
                f"https://{server}/auth/oauth2/revoke-token",
                headers=revoke_headers,
                data=revoke_payload,
                verify=False
            )
            
            if revoke_response.status_code == 200:
                log_with_ui("Successfully signed out and revoked token")
            else:
                log_with_ui(f"Sign out failed with status code: {revoke_response.status_code}")
                
        except Exception as e:
            log_with_ui(f"Error during sign out: {str(e)}")
        
        # Save the updated users back to the file (if needed)
        temp_users_path = Path(__file__).parent.parent / "temp_users.json"
        try:
            with open(temp_users_path, 'r') as f:
                all_users = json.load(f)
                
            # Update the emails in the full user list
            for i, user in enumerate(all_users):
                user_id = user.get('id', '')
                # Find matching updated user
                updated_user = next((u for u in external_users if u.get('UserID') == user_id and 
                                    u.get('Email') != u.get('NewEmail')), None)
                if updated_user and updated_user.get('NewEmail'):
                    all_users[i]['email'] = updated_user.get('NewEmail')
            
            # Save back to file
            with open(temp_users_path, 'w') as f:
                json.dump(all_users, f, indent=2)
            log_message(f"Successfully saved updated user data to {temp_users_path}")
        except Exception as e:
            log_message(f"Note: Updated users were not saved back to temp file: {str(e)}")
        
        # Final stats
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        duration_str = str(duration).split('.')[0]  # Remove microseconds
        
        stats_message = (
            f"Email update process completed: {success_count} succeeded, {failed_count} failed\n"
            f"Total time: {duration_str}\n"
            f"Success rate: {success_count/len(external_users)*100:.1f}%"
        )
        log_with_ui(stats_message, is_success=True)
        
        # Log completion
        log_function_execution("email_updater", "COMPLETE", {
            "updated_count": success_count,
            "failed_count": failed_count,
            "message": stats_message.split('\n')[0]  # Just use first line
        })
        
        # If we have a progress dialog, keep it open a moment, then close
        if progress_widget:
            try:
                # Display summary in current operation
                progress_widget['current_op'].setText(f"Update completed: {success_count} succeeded, {failed_count} failed")
                QApplication.processEvents()
                
                # Wait 2 seconds then close
                QTimer.singleShot(2000, progress_widget['dialog'].close)
            except Exception:
                pass
        
        # Show final message box
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(None, "Update Complete", stats_message)
        
        # Return the updated users
        return sanitized_users
            
    except Exception as e:
        error_msg = f"Error in email update process: {str(e)}"
        log_message(error_msg)
        log_function_execution("email_updater", "FAILED", {
            "error": error_msg
        })
        
        # Close the progress dialog if it exists
        if 'progress_widget' in locals() and progress_widget:
            try:
                progress_widget['dialog'].close()
            except Exception:
                pass
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Error", error_msg)
        return sanitized_users  # Return original data on failure


if __name__ == '__main__':
    # For standalone testing
    import sys
    app = QApplication(sys.argv)
    
    # Test with dummy data
    dummy_users = [
        {
            "UserID": "user1", 
            "FullName": "User One", 
            "Email": "user1@internal.com", 
            "NewEmail": "",
            "Classification": "Internal"
        },
        {
            "UserID": "user2", 
            "FullName": "User Two", 
            "Email": "user2@external.com", 
            "NewEmail": "user2@external.com.Ext",
            "Classification": "External"
        }
    ]
    
    page = EmailUpdaterPage(dummy_users)
    page.show()
    
    sys.exit(app.exec())