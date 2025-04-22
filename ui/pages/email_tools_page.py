from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QStackedWidget, QMessageBox
from ..components.tool_card import ToolCard
from scripts.email_sanitizer import EmailSanitizerPage, sanitize_emails
from scripts.user_retriever import UserRetriever
from pathlib import Path
import json
from ..state import AuthState
from ..utils import create_styled_message_box

class EmailToolsPage(QWidget):
    def __init__(self):
        super().__init__()
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(12)
        
        # Create stacked widget to switch between tool cards and sanitizer page
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
        
        # Create sanitizer page (second page in stack)
        self.sanitizer_page = EmailSanitizerPage()
        self.sanitizer_page.back_to_tools_clicked.connect(self.show_tools)
        
        # Add both pages to stack
        self.stack.addWidget(self.tools_widget)
        self.stack.addWidget(self.sanitizer_page)
        
        # Add stack to main layout
        self.main_layout.addWidget(self.stack)
        
        # Start with tools page
        self.stack.setCurrentWidget(self.tools_widget)
    
    def open_sanitizer(self):
        """Open the email sanitizer page"""
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
                users = retriever.get_user_list()
                # Store users in a temporary file for the sanitizer script
                temp_path = Path(__file__).parent.parent.parent / 'temp_users.json'
                with open(temp_path, 'w') as f:
                    json.dump(users, f)
                
                # Now get the saved users via sanitize_emails
                loaded_users = sanitize_emails()
                if loaded_users:
                    # Load data into sanitizer page
                    self.sanitizer_page.load_data(loaded_users)
                    # Switch to sanitizer page
                    self.stack.setCurrentWidget(self.sanitizer_page)
            except Exception as e:
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