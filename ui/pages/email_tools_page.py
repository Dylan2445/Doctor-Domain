from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QStackedWidget, QMessageBox, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox, QFrame, QPushButton, QLineEdit, QSizePolicy, QScrollArea, QProgressBar
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QTimer
# Change relative imports to absolute imports
from ui.components.tool_card import ToolCard
from scripts.email_sanitizer import sanitize_emails
from scripts.email_updater import update_emails
from scripts.user_retriever import UserRetriever
from pathlib import Path
import json
import time
from ui.state import AuthState
from ui.utils import create_styled_message_box, log_message

class EmailToolsPage(QWidget):
    def __init__(self):
        super().__init__()
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(12)
        
        # Create stacked widget to switch between tool cards and pages
        self.stack = QStackedWidget()
        
        # Create tools widget (first page in stack)
        self.tools_widget = QWidget()
        tools_layout = QVBoxLayout(self.tools_widget)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(12)

        # Header
        header = QLabel("Email Management Tools")
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
            padding-bottom: 5px;
        """)
        tools_layout.addWidget(header)

        # Cards
        cards_widget = QWidget()
        cards_layout = QVBoxLayout(cards_widget)
        cards_layout.setSpacing(15)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        # Function cards container
        functions_widget = QWidget()
        functions_layout = QHBoxLayout(functions_widget)
        functions_layout.setSpacing(15)
        functions_layout.setContentsMargins(0, 0, 0, 0)

        # Create custom sanitizer card that calls our integrated sanitizer
        sanitizer_card = ToolCard(
            "Email Sanitizer 🧼",
            "Finds and updates any user email addresses that are not intended domains.",
            "sanitize.png",
            None  # No script path
        )
        sanitizer_card.run_btn.setText("Run Tool")
        sanitizer_card.run_btn.setEnabled(True)
        sanitizer_card.run_btn.clicked.connect(self.open_sanitizer)
        
        injector_card = ToolCard(
            "Email Injector 💉",
            "Updates all accounts missing an email address by assigning a placeholder domain.",
            "inject.png",
            "scripts/email_injector.py"
        )

        functions_layout.addWidget(sanitizer_card)
        functions_layout.addWidget(injector_card)
        cards_layout.addWidget(functions_widget)

        # Coming soon card
        coming_soon_card = ToolCard(
            "Additional Tools Coming Soon ⏳",
            "New Features Coming Soon!",
            "soon.png",
            None
        )
        cards_layout.addWidget(coming_soon_card)

        tools_layout.addWidget(cards_widget)
        tools_layout.addStretch()
        
        # Create simplified email sanitizer page
        self.sanitizer_page = self.create_sanitizer_page()
        self.processing_page = self.create_processing_page()
        
        # Add all pages to stack
        self.stack.addWidget(self.tools_widget)       # Index 0
        self.stack.addWidget(self.sanitizer_page)     # Index 1
        self.stack.addWidget(self.processing_page)    # Index 2
        
        # Add stack to main layout
        self.main_layout.addWidget(self.stack)
        
        # Start with tools page
        self.stack.setCurrentWidget(self.tools_widget)
        
        # Store users and processing results
        self.users = []
        self.sanitized_users = None
        self.external_users = None
    
    def create_sanitizer_page(self):
        """Create a clean, minimalist configuration page for email sanitizer"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)  # Reduced margins
        layout.setSpacing(10)  # Even more reduced spacing
        
        # Create a header with title and description inline to save vertical space
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title with more compact styling
        title = QLabel("Email Sanitizer")
        title.setStyleSheet("""
            font-size: 22px; 
            font-weight: 600; 
            color: #1E293B;
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Add header to main layout
        layout.addWidget(header_widget)
        
        # Simple description - more compact
        description = QLabel("Identify and update external user email addresses by appending '.Ext'")
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: #64748B; 
            font-size: 13px;
            margin-bottom: 5px;
        """)
        layout.addWidget(description)
        
        # Main content in a clean card with reduced padding
        content_card = QWidget()
        content_card.setObjectName("contentCard")
        content_card.setStyleSheet("""
            #contentCard {
                background-color: white;
                border-radius: 8px;
            }
        """)
        
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(15, 15, 15, 15)  # Even more reduced padding
        content_layout.setSpacing(10)  # Reduced spacing
        
        # More compact section title
        config_title = QLabel("Domain Configuration")
        config_title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1E293B;
            margin-bottom: 2px;
        """)
        
        # Option selection with clean styling
        options_container = QWidget()
        options_layout = QVBoxLayout(options_container)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(6)  # More reduced spacing
        
        # Option label inline with options to save space
        option_header = QWidget()
        option_header_layout = QHBoxLayout(option_header)
        option_header_layout.setContentsMargins(0, 0, 0, 0)
        option_header_layout.setSpacing(0)
        
        option_label = QLabel("Select a domain detection method:")
        option_label.setStyleSheet("color: #64748B; font-size: 13px;")
        
        option_header_layout.addWidget(option_label)
        option_header_layout.addStretch()
        
        options_layout.addWidget(option_header)
        
        # Radio buttons with reduced height for compactness
        self.manual_radio = QPushButton("Provide company domains manually")
        self.manual_radio.setCheckable(True)
        self.manual_radio.setChecked(True)
        self.manual_radio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manual_radio.setMinimumHeight(34)  # Even more reduced height
        self.manual_radio.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 0 15px;
                background-color: white;
                border-radius: 6px;
                font-size: 13px;
                color: #334155;
                font-weight: 500;
                border: 1px solid #E2E8F0;
            }
            QPushButton:checked {
                background-color: #F8FAFC;
                border: 1px solid #3B82F6;
                color: #1E40AF;
            }
            QPushButton:hover:!checked {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
            }
        """)
        
        self.auto_radio = QPushButton("Automatically detect company domains")
        self.auto_radio.setCheckable(True)
        self.auto_radio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_radio.setMinimumHeight(34)  # Even more reduced height
        self.auto_radio.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 0 15px;
                background-color: white;
                border-radius: 6px;
                font-size: 13px;
                color: #334155;
                font-weight: 500;
                border: 1px solid #E2E8F0;
            }
            QPushButton:checked {
                background-color: #F8FAFC;
                border: 1px solid #3B82F6;
                color: #1E40AF;
            }
            QPushButton:hover:!checked {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
            }
        """)
        
        # Make buttons exclusive
        self.manual_radio.clicked.connect(lambda: self.toggle_radio_buttons(True))
        self.auto_radio.clicked.connect(lambda: self.toggle_radio_buttons(False))
        
        options_layout.addWidget(self.manual_radio)
        options_layout.addWidget(self.auto_radio)
        
        # Domain input with clean styling
        self.domain_section = QWidget()
        domain_layout = QVBoxLayout(self.domain_section)
        domain_layout.setContentsMargins(0, 3, 0, 0)
        domain_layout.setSpacing(3)  # Reduced spacing
        
        # Combine domain label and hint in a more compact way
        domain_header = QWidget()
        domain_header_layout = QHBoxLayout(domain_header)
        domain_header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Domain label
        domain_label = QLabel("Enter company domains:")
        domain_label.setStyleSheet("color: #64748B; font-size: 13px;")
        
        domain_header_layout.addWidget(domain_label)
        domain_header_layout.addStretch()
        
        domain_layout.addWidget(domain_header)
        
        # Domain input with cleaner styling and reduced height
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("e.g., company.com, example.org")
        self.domain_input.setMinimumHeight(32)  # Even more reduced height
        self.domain_input.setStyleSheet("""
            QLineEdit {
                padding: 0 10px;
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                font-size: 13px;
                color: #334155;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
        """)
        
        # Domain hint as placeholderText and below input, smaller font
        domain_hint = QLabel("Separate multiple domains with commas")
        domain_hint.setStyleSheet("color: #94A3B8; font-size: 11px; font-style: italic;")
        
        domain_layout.addWidget(self.domain_input)
        domain_layout.addWidget(domain_hint)
        
        # Info card with more compact design
        info_card = QWidget()
        info_card.setObjectName("infoCard")
        info_card.setStyleSheet("""
            #infoCard {
                background-color: #F0F9FF;
                border-radius: 6px;
            }
        """)
        
        info_layout = QHBoxLayout(info_card)
        info_layout.setContentsMargins(8, 6, 8, 6)  # Even more reduced padding
        
        info_icon = QLabel("ℹ️")
        info_icon.setStyleSheet("font-size: 14px;")  # Smaller icon
        
        info_text = QLabel("Only disabled user accounts will be processed. The tool will identify external emails and append '.Ext'.")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #0C4A6E; font-size: 11px; line-height: 1.1;")  # Smaller text
        
        info_layout.addWidget(info_icon, alignment=Qt.AlignmentFlag.AlignTop)
        info_layout.addWidget(info_text, 1)

        # View All Users button
        view_users_btn = QPushButton("View All Users")
        view_users_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_users_btn.setMinimumHeight(32)
        view_users_btn.setStyleSheet("""
            QPushButton {
                background-color: #EFF6FF;
                color: #1E40AF;
                border: 1px solid #BFDBFE;
                border-radius: 6px;
                padding: 0 15px;
                font-size: 13px;
                font-weight: 500;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #DBEAFE;
                border-color: #93C5FD;
            }
        """)
        view_users_btn.clicked.connect(self.show_all_users)
        
        # Add components to content layout in a compact way
        content_layout.addWidget(config_title)
        content_layout.addWidget(options_container)
        content_layout.addWidget(self.domain_section)
        content_layout.addWidget(info_card)
        content_layout.addWidget(view_users_btn) # Added view users button
        
        # Action buttons with clean design
        actions_container = QWidget()
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 10, 0, 0)
        
        back_btn = QPushButton("Back to Tools")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setMinimumHeight(34)  # Even more reduced height
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 0 15px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }
        """)
        back_btn.clicked.connect(self.show_tools)
        
        process_btn = QPushButton("Process Emails")
        process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        process_btn.setMinimumHeight(34)  # Even more reduced height
        process_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 15px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1E40AF;
            }
        """)
        process_btn.clicked.connect(self.process_emails)
        
        actions_layout.addWidget(back_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(process_btn)
        
        # Add all to main layout - use fixed layout instead of stretch to eliminate blank space
        layout.addWidget(content_card)
        layout.addWidget(actions_container)
        
        return page
    
    def create_processing_page(self):
        """Create a processing page that shows results and handles updates"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)
        
        # Clean header with title only
        title = QLabel("Email Processing")
        title.setStyleSheet("""
            font-size: 28px; 
            font-weight: 600; 
            color: #1E293B;
        """)
        
        # Main content in a clean card
        content_card = QWidget()
        content_card.setObjectName("contentCard")
        content_card.setStyleSheet("""
            #contentCard {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)
        
        # Status section at the top
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Processing emails...")
        self.status_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #1E293B;
        """)
        
        self.status_pill = QLabel("Processing")
        self.status_pill.setStyleSheet("""
            background-color: #DBEAFE;
            color: #2563EB;
            border-radius: 15px;
            padding: 4px 12px;
            font-size: 14px;
            font-weight: 500;
        """)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.status_pill)
        status_layout.addStretch()
        
        content_layout.addWidget(status_container)
        
        # Progress section
        progress_container = QWidget()
        self.progress_layout = QVBoxLayout(progress_container)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(15)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #F1F5F9;
                text-align: center;
                padding: 0px;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 5px;
            }
        """)
        
        # Progress text
        self.progress_text = QLabel("Starting process...")
        self.progress_text.setStyleSheet("color: #64748B; font-size: 14px;")
        
        self.progress_layout.addWidget(self.progress_bar)
        self.progress_layout.addWidget(self.progress_text)
        
        content_layout.addWidget(progress_container)
        
        # Results section
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_layout.setContentsMargins(0, 10, 0, 0)
        results_layout.setSpacing(20)
        
        # Table header
        table_header = QWidget()
        table_header_layout = QHBoxLayout(table_header)
        table_header_layout.setContentsMargins(0, 0, 0, 0)
        
        results_title = QLabel("Email Updates")
        results_title.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: #1E293B;
        """)
        
        self.results_count = QLabel("0 users")
        self.results_count.setStyleSheet("""
            background-color: #EFF6FF;
            color: #2563EB;
            border-radius: 15px;
            padding: 4px 12px;
            font-size: 14px;
            font-weight: 500;
        """)
        
        table_header_layout.addWidget(results_title)
        table_header_layout.addWidget(self.results_count)
        table_header_layout.addStretch()
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["User ID", "Name", "Original Email", "New Email"])
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #F1F5F9;
                outline: none;
            }
            QTableWidget::item {
                padding: 14px 8px;
                border-bottom: 1px solid #F1F5F9;
                color: #334155;
                font-size: 14px;
            }
            QTableWidget::item:selected {
                background-color: #F0F9FF;
                color: #0369A1;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                padding: 15px 8px;
                font-weight: 600;
                color: #64748B;
                font-size: 14px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                text-align: left;
            }
        """)
        
        # Configure table for better appearance
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setShowGrid(False)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setMinimumHeight(300)
        
        results_layout.addWidget(table_header)
        results_layout.addWidget(self.results_table)
        
        # Summary section at bottom (initially hidden)
        self.summary_container = QWidget()
        summary_layout = QHBoxLayout(self.summary_container)
        summary_layout.setContentsMargins(0, 10, 0, 0)
        
        self.summary_icon = QLabel("✅")
        self.summary_icon.setStyleSheet("font-size: 24px;")
        
        self.summary_text = QLabel("Process completed successfully")
        self.summary_text.setStyleSheet("""
            font-size: 16px;
            font-weight: 500;
            color: #059669;
        """)
        
        summary_layout.addWidget(self.summary_icon)
        summary_layout.addWidget(self.summary_text)
        summary_layout.addStretch()
        
        self.summary_container.setVisible(False)  # Initially hidden
        
        content_layout.addWidget(results_container)
        content_layout.addWidget(self.summary_container)
        
        # Action buttons with clean design
        actions_container = QWidget()
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        self.back_to_tools_btn = QPushButton("Back to Tools")
        self.back_to_tools_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_to_tools_btn.setMinimumHeight(50)
        self.back_to_tools_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #64748B;
                border: 2px solid #E2E8F0;
                border-radius: 10px;
                padding: 0 30px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }
        """)
        self.back_to_tools_btn.clicked.connect(self.show_tools)
        
        actions_layout.addStretch()
        actions_layout.addWidget(self.back_to_tools_btn)
        
        # Add all to main layout
        layout.addWidget(title)
        layout.addWidget(content_card, 1)
        layout.addWidget(actions_container)
        
        return page
    
    def open_sanitizer(self):
        """Open the email sanitizer tool"""
        # Check if user is logged in
        auth_state = AuthState.instance()
        if not auth_state.is_logged_in:
            msg_box = create_styled_message_box(
                self,
                title="Not Logged In",
                text="Please log in first to use this tool.",
                icon=QMessageBox.Icon.Warning
            )
            msg_box.exec()
            return
            
        if not auth_state.access_token:
            msg_box = create_styled_message_box(
                self,
                title="Authentication Error",
                text="No access token found. Please log in again.",
                icon=QMessageBox.Icon.Warning
            )
            msg_box.exec()
            return
        
        try:
            # Load settings to get server, library ID and customer ID
            config_path = Path(__file__).parent.parent.parent / 'config' / 'login_settings.json'
            if not config_path.exists():
                msg_box = create_styled_message_box(
                    self,
                    title="Configuration Error",
                    text="Login settings not found. Please configure your account first.",
                    icon=QMessageBox.Icon.Critical
                )
                msg_box.exec()
                return
                
            with open(config_path) as f:
                settings = json.load(f)
                
            server = settings.get('Server')
            library_id = settings.get('Library ID')
            customer_id = settings.get('Customer ID')
            
            if not all([server, library_id, customer_id]):
                msg_box = create_styled_message_box(
                    self,
                    title="Configuration Error",
                    text="Missing server, customer ID or library ID in settings.",
                    icon=QMessageBox.Icon.Critical
                )
                msg_box.exec()
                return
            
            # Fetch user list
            retriever = UserRetriever(server, auth_state.access_token, customer_id, library_id)
            try:
                # Show a styled message box while loading
                progress_msg = create_styled_message_box(
                    self,
                    title="Loading",
                    text="Retrieving user data from server...",
                    icon=QMessageBox.Icon.Information,
                    buttons=QMessageBox.StandardButton.NoButton
                )
                progress_msg.show()
                
                # Get users from server
                self.users = retriever.get_user_list()
                
                # Store users in a temporary file for the sanitizer script
                temp_path = Path(__file__).parent.parent.parent / 'temp_users.json'
                with open(temp_path, 'w') as f:
                    json.dump(self.users, f)
                
                # Close progress dialog
                progress_msg.accept()
                
                # Switch to sanitizer page
                self.stack.setCurrentWidget(self.sanitizer_page)
                
            except Exception as e:
                # Close progress dialog if open
                progress_msg.accept()
                
                # Enhanced error message with more context
                error_details = f"""Failed to retrieve users: {str(e)}

Server URL: https://{server}
Customer ID: {customer_id}
Library ID: {library_id}
Request URL: https://{server}/work/api/v2/customers/{customer_id}/libraries/{library_id}/users
"""
                msg_box = create_styled_message_box(
                    self,
                    title="Error Retrieving Users",
                    text=error_details,
                    icon=QMessageBox.Icon.Critical
                )
                msg_box.exec()
                
        except Exception as e:
            msg_box = create_styled_message_box(
                self,
                title="Error",
                text=f"Failed to run email sanitizer: {str(e)}",
                icon=QMessageBox.Icon.Critical
            )
            msg_box.exec()
    
    def show_tools(self):
        """Show the tools page"""
        self.stack.setCurrentWidget(self.tools_widget)
    
    def toggle_radio_buttons(self, manual_selected):
        """Toggle between manual and automatic domain detection methods"""
        if manual_selected:
            self.manual_radio.setChecked(True)
            self.auto_radio.setChecked(False)
            self.domain_section.setVisible(True)
        else:
            self.manual_radio.setChecked(False)
            self.auto_radio.setChecked(True)
            self.domain_section.setVisible(False)
    
    def process_emails(self):
        """Process emails directly with simplified workflow"""
        # Update UI to indicate processing
        self.stack.setCurrentWidget(self.processing_page)
        self.status_label.setText("Processing emails...")
        self.status_pill.setText("Processing")
        self.status_pill.setStyleSheet("""
            background-color: #DBEAFE;
            color: #2563EB;
            border-radius: 15px;
            padding: 4px 12px;
            font-size: 14px;
            font-weight: 500;
        """)
        self.progress_text.setText("Analyzing emails...")
        self.progress_bar.setValue(10)
        self.summary_container.setVisible(False)
        self.back_to_tools_btn.setEnabled(False)
        
        # Get settings for server connection from config file
        try:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'login_settings.json'
            with open(config_path) as f:
                settings = json.load(f)
                
            server = settings.get('Server')
            library_id = settings.get('Library ID')
            customer_id = settings.get('Customer ID')
            
            # Get authentication token
            auth_state = AuthState.instance()
            access_token = auth_state.access_token
            
            # Get the selected detection method and domains
            use_manual_domains = self.manual_radio.isChecked()
            
            # Import directly from email_sanitizer.py
            from scripts.email_sanitizer import domain_provided_route, domain_discovery_route
            
            # Process with 20% progress
            self.progress_bar.setValue(20)
            self.progress_text.setText("Identifying external email addresses...")
            
            if use_manual_domains:
                # Get the domain list from input
                domains_input = self.domain_input.text().strip()
                provided_domains = [d.strip() for d in domains_input.split(',') if d.strip()]
                
                if not provided_domains:
                    self.show_error_and_return("Input Error", "Please enter at least one domain.")
                    return
                
                # Process with provided domains
                self.sanitized_users = domain_provided_route(self.users, provided_domains)
            else:
                # Use auto-discovery
                self.sanitized_users = domain_discovery_route(self.users)
            
            # Update progress to 40%
            self.progress_bar.setValue(40)
            self.progress_text.setText("Finding external users to update...")
            
            # Find external users with new emails
            self.external_users = [user for user in self.sanitized_users 
                                  if user.get("Classification") == "External" and user.get("NewEmail")]
            
            if not self.sanitized_users:
                self.show_completed_with_no_updates("No Results", 
                                                "No disabled users found that need email sanitization.")
                return
            
            if not self.external_users:
                self.show_completed_with_no_updates("No Updates Required", 
                                                "No external users with new email addresses were found.")
                return
            
            # Update progress to 50%
            self.progress_bar.setValue(50)
            self.progress_text.setText("Preparing to update emails...")
            
            # Populate the results table
            self.populate_results_table(self.external_users)
            
            # Update progress to 60% and prepare for confirmation
            self.progress_bar.setValue(60)
            self.progress_text.setText(f"Ready to update {len(self.external_users)} email addresses...")
            
            # Show confirmation dialog
            confirm = create_styled_message_box(
                self,
                title="Confirm Email Updates",
                text=f"You are about to update {len(self.external_users)} email addresses. Continue?",
                icon=QMessageBox.Icon.Question,
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm.exec() != QMessageBox.StandardButton.Yes:
                self.progress_text.setText("Operation cancelled by user")
                self.status_pill.setText("Cancelled")
                self.status_pill.setStyleSheet("""
                    background-color: #FEF2F2;
                    color: #B91C1C;
                    border-radius: 15px;
                    padding: 4px 12px;
                    font-size: 14px;
                    font-weight: 500;
                """)
                self.back_to_tools_btn.setEnabled(True)
                return
            
            # Update progress to 70%
            self.progress_bar.setValue(70)
            self.progress_text.setText("Processing updates...")
            
            # Process the updates
            try:
                # Log that we're about to call the update_emails function
                log_message("DEBUG: About to call update_emails function")
                
                # Pass the connection settings directly to the update_emails function
                # This is a clean approach that doesn't modify the login_settings.json file
                from scripts.email_updater import update_emails
                
                # Log the server we're using for debug purposes
                log_message(f"DEBUG: Using server: {server}")
                
                # Actually call the update_emails function from the email_updater module
                updated_users = update_emails(self.external_users)
                log_message(f"DEBUG: update_emails function returned {len(updated_users) if updated_users else 0} users")
                
                # For debug purposes, log a sample of the first user if available
                if updated_users and len(updated_users) > 0:
                    sample_user = updated_users[0]
                    log_message(f"DEBUG: Sample updated user - UserID: {sample_user.get('UserID', 'N/A')}, Email: {sample_user.get('Email', 'N/A')}")
                
                # Loop through external users and update progress on UI
                for i, user in enumerate(self.external_users):
                    # Update UI
                    progress_percent = 70 + int((i / len(self.external_users)) * 25)
                    self.progress_bar.setValue(progress_percent)
                    self.progress_text.setText(f"Updating {i+1} of {len(self.external_users)}: {user.get('FullName')}")
                    
                    # Wait a bit to avoid overwhelming the server
                    if i > 0 and i % 10 == 0:
                        self.progress_text.setText(f"Pausing briefly to avoid server overload...")
                        time.sleep(2)
                
                # Update completed successfully
                self.progress_bar.setValue(100)
                self.progress_text.setText(f"Successfully updated {len(self.external_users)} email addresses")
                self.status_label.setText("Email update complete")
                self.status_pill.setText("Completed")
                self.status_pill.setStyleSheet("""
                    background-color: #ECFDF5;
                    color: #059669;
                    border-radius: 15px;
                    padding: 4px 12px;
                    font-size: 14px;
                    font-weight: 500;
                """)
                
                # Show summary
                self.summary_container.setVisible(True)
                self.summary_text.setText(f"Successfully updated {len(self.external_users)} email addresses")
                self.back_to_tools_btn.setEnabled(True)
                
                # Log the successful operation
                log_message(f"Email sanitizer completed: {len(self.external_users)} emails updated")
                
            except Exception as e:
                self.show_error_and_return("Update Error", f"Error updating emails: {str(e)}")
                log_message(f"Email update error: {str(e)}")
                
        except Exception as e:
            self.show_error_and_return("Processing Error", f"Error processing emails: {str(e)}")
            log_message(f"Email processing error: {str(e)}")
    
    def populate_results_table(self, users):
        """Populate the results table with user data"""
        # Clear and set row count
        self.results_table.setRowCount(0)
        self.results_table.setRowCount(len(users))
        
        # Update count label
        self.results_count.setText(f"{len(users)} users")
        
        # Add users to table
        for i, user in enumerate(users):
            # Create table items
            user_id = QTableWidgetItem(str(user.get("UserID", "")))
            name = QTableWidgetItem(user.get("FullName", ""))
            email = QTableWidgetItem(user.get("Email", ""))
            new_email = QTableWidgetItem(user.get("NewEmail", ""))
            
            # Set color for new email
            new_email.setForeground(QColor("#059669"))  # Green text
            
            # Add to table
            self.results_table.setItem(i, 0, user_id)
            self.results_table.setItem(i, 1, name)
            self.results_table.setItem(i, 2, email)
            self.results_table.setItem(i, 3, new_email)
            
            # Set row height
            self.results_table.setRowHeight(i, 40)
    
    def show_error_and_return(self, title, message):
        """Show error and update UI"""
        # Update processing page
        self.status_label.setText("Error")
        self.status_pill.setText("Failed")
        self.status_pill.setStyleSheet("""
            background-color: #FEF2F2;
            color: #B91C1C;
            border-radius: 15px;
            padding: 4px 12px;
            font-size: 14px;
            font-weight: 500;
        """)
        self.progress_text.setText(message)
        self.back_to_tools_btn.setEnabled(True)
        
        # Show error dialog
        msg_box = create_styled_message_box(
            self,
            title=title,
            text=message,
            icon=QMessageBox.Icon.Critical
        )
        msg_box.exec()
    
    def show_completed_with_no_updates(self, title, message):
        """Show completion status when no updates are needed"""
        # Update processing page
        self.status_label.setText("No updates needed")
        self.status_pill.setText("Completed")
        self.status_pill.setStyleSheet("""
            background-color: #F0F9FF;
            color: #0369A1;
            border-radius: 15px;
            padding: 4px 12px;
            font-size: 14px;
            font-weight: 500;
        """)
        self.progress_bar.setValue(100)
        self.progress_text.setText(message)
        self.summary_container.setVisible(True)
        self.summary_icon.setText("ℹ️")
        self.summary_text.setText(message)
        self.summary_text.setStyleSheet("""
            font-size: 16px;
            font-weight: 500;
            color: #0369A1;
        """)
        self.back_to_tools_btn.setEnabled(True)
        
        # Show info dialog
        msg_box = create_styled_message_box(
            self,
            title=title,
            text=message,
            icon=QMessageBox.Icon.Information
        )
        msg_box.exec()
    
    def show_all_users(self):
        """Show a dialog with all users in a table"""
        if not self.users:
            msg_box = create_styled_message_box(
                self,
                title="No Users",
                text="No users have been loaded yet.",
                icon=QMessageBox.Icon.Information
            )
            msg_box.exec()
            return
            
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("All Users")
        dialog.setMinimumSize(800, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("All Users")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #1E293B;
        """)
        
        # User count pill
        count_container = QWidget()
        count_layout = QHBoxLayout(count_container)
        count_layout.setContentsMargins(0, 0, 0, 0)
        
        count_label = QLabel(f"Total: {len(self.users)} users")
        count_label.setStyleSheet("""
            background-color: #EFF6FF;
            color: #2563EB;
            border-radius: 15px;
            padding: 4px 12px;
            font-size: 13px;
            font-weight: 500;
        """)
        
        count_layout.addWidget(count_label)
        count_layout.addStretch()
        
        # Table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["User ID", "Name", "Email", "Status", "Type"])
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #F1F5F9;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F1F5F9;
                color: #334155;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #F0F9FF;
                color: #0369A1;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                padding: 10px 8px;
                font-weight: 600;
                color: #64748B;
                font-size: 13px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                text-align: left;
            }
        """)
        
        # Configure table for better appearance
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Populate table
        table.setRowCount(len(self.users))
        for i, user in enumerate(users := self.users):
            # Create table items
            user_id = QTableWidgetItem(str(user.get("UserID", "")))
            name = QTableWidgetItem(user.get("FullName", ""))
            email = QTableWidgetItem(user.get("Email", ""))
            
            # Get status
            status_text = "Enabled" if user.get("Active", False) else "Disabled"
            status = QTableWidgetItem(status_text)
            
            # Set color based on status
            if status_text == "Enabled":
                status.setForeground(QColor("#059669"))  # Green
            else:
                status.setForeground(QColor("#DC2626"))  # Red
                
            # User type based on email domain
            user_email = user.get("Email", "")
            user_type = QTableWidgetItem("Unknown")
            
            if user_email:
                # Get domain from provided domains if available
                if hasattr(self, 'domain_input') and self.domain_input.text().strip():
                    domains = [d.strip() for d in self.domain_input.text().split(',') if d.strip()]
                    is_external = True
                    
                    try:
                        email_domain = user_email.split('@')[1].lower()
                        for domain in domains:
                            if email_domain == domain.lower() or email_domain.endswith('.' + domain.lower()):
                                is_external = False
                                break
                                
                        user_type = QTableWidgetItem("External" if is_external else "Internal")
                        if is_external:
                            user_type.setForeground(QColor("#0369A1"))  # Blue
                        else:
                            user_type.setForeground(QColor("#059669"))  # Green
                    except:
                        pass
                else:
                    # Just show if it has .Ext suffix
                    if user_email.lower().endswith('.ext'):
                        user_type = QTableWidgetItem("External")
                        user_type.setForeground(QColor("#0369A1"))  # Blue
            
            # Add to table
            table.setItem(i, 0, user_id)
            table.setItem(i, 1, name)
            table.setItem(i, 2, email)
            table.setItem(i, 3, status)
            table.setItem(i, 4, user_type)
            
            # Set row height
            table.setRowHeight(i, 36)
        
        # Button to close the dialog
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }
        """)
        button_box.rejected.connect(dialog.reject)
        
        # Add components to layout
        layout.addWidget(header)
        layout.addWidget(count_container)
        layout.addWidget(table)
        layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Show dialog
        dialog.exec()