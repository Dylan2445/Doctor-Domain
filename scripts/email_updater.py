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
from ui.utils import log_function_execution, create_styled_message_box

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
        # Get count of users to update
        external_users = [user for user in self.sanitized_users if user.get("Classification") == "External"]
        if not external_users:
            QMessageBox.information(self, "No Users to Update", "No external users found to update.")
            return
        
        # Create a dialog with the list of users to update
        dialog = QDialog(self)
        dialog.setWindowTitle("Confirm Email Updates")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        dialog.setStyleSheet("background-color: white;")
        
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
        
        # Show dialog and process result
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.update_emails()
    
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
        self.update_btn.setEnabled(False)
        self.back_btn.setEnabled(False)
        QApplication.processEvents()
        
        # Start update operation
        self.log_message("Starting email update for users...")
        
        # Determine API base URL
        base_url = f"https://{self.server}/api/v2/customers/{self.customer_id}"
        if not self.server.lower().endswith("cloudimanage.com"):
            base_url = f"{base_url}/libraries/{self.library}"
        
        update_count = 0
        success_count = 0
        failed_count = 0
        
        try:
            for i, user in enumerate(external_users):
                user_id = user.get("UserID", "")
                new_email = user.get("NewEmail", "")
                
                if user_id and new_email:
                    # Update progress
                    self.progress_bar.setValue(i)
                    self.progress_label.setText(f"Updating user {i+1} of {len(external_users)}: {user_id}")
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
                        response = requests.patch(
                            update_url,
                            headers=self.headers,
                            json=payload,
                            verify=False
                        )
                        
                        # Process response
                        if response.status_code in [200, 201, 204]:
                            success_message = f"User update successful: {user_id}"
                            self.log_message(success_message)
                            success_count += 1
                        else:
                            error_message = f"User update failed: {user_id} - Status: {response.status_code}"
                            if response.text:
                                error_message += f" - {response.text}"
                            self.log_message(error_message)
                            failed_count += 1
                        
                        # Rate limiting - pause to avoid overwhelming server
                        update_count += 1
                        if update_count % self.rate_limit == 0:
                            pause_message = f"Pausing for {self.pause_time} seconds to avoid system overload..."
                            self.log_message(pause_message)
                            self.progress_label.setText(pause_message)
                            QApplication.processEvents()
                            time.sleep(self.pause_time)
                            
                    except Exception as e:
                        self.log_message(f"Error updating user {user_id}: {str(e)}")
                        failed_count += 1
            
            # Final progress update
            self.progress_bar.setValue(len(external_users))
            result_message = f"Update completed: {success_count} succeeded, {failed_count} failed"
            self.progress_label.setText(result_message)
            self.log_message("Email update process completed for all users.")
            
            # Show results message
            QMessageBox.information(self, "Update Complete", result_message)
            
        except Exception as e:
            self.log_message(f"Error during email update: {str(e)}")
            QMessageBox.critical(self, "Update Error", f"An error occurred: {str(e)}")
        finally:
            # Clean up
            self.sign_out()
            
            # Re-enable buttons
            self.update_btn.setEnabled(True)
            self.back_btn.setEnabled(True)
            self.status_label.setText("Email update completed")
    
    def log_message(self, message):
        """Write a message to the log file"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp} - {message}"
            
            with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"{log_entry}\n")
                
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
    from ui.utils import log_function_execution
    
    try:
        # Log start of email update process
        log_function_execution("email_updater", "START", {
            "users_count": len(sanitized_users)
        })
        
        # Return the users for the UI to handle
        return sanitized_users
            
    except Exception as e:
        error_msg = f"Error preparing email update: {str(e)}"
        log_function_execution("email_updater", "FAILED", {
            "error": error_msg
        })
        QMessageBox.critical(None, "Error", error_msg)
        return None


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