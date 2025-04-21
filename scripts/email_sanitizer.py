import json
import os
import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                           QTableWidget, QTableWidgetItem, QRadioButton,
                           QLineEdit, QMessageBox, QGroupBox, QHBoxLayout,
                           QHeaderView, QProgressBar, QApplication, QFrame,
                           QStackedWidget, QSizePolicy, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIcon

def get_levenshtein_distance(string1, string2, case_sensitive=False, normalize_output=False):
    """
    Calculate the Levenshtein distance between two strings.
    """
    if not case_sensitive:
        string1 = string1.lower()
        string2 = string2.lower()
    
    # Create a matrix of size (len(string1)+1) x (len(string2)+1)
    d = [[0 for _ in range(len(string2) + 1)] for _ in range(len(string1) + 1)]
    
    # Initialize the first row and column
    for i in range(len(string1) + 1):
        d[i][0] = i
    for j in range(len(string2) + 1):
        d[0][j] = j
    
    # Fill the matrix
    for i in range(1, len(string1) + 1):
        for j in range(1, len(string2) + 1):
            cost = 0 if string1[i-1] == string2[j-1] else 1
            d[i][j] = min(
                d[i-1][j] + 1,      # deletion
                d[i][j-1] + 1,      # insertion
                d[i-1][j-1] + cost  # substitution
            )
    
    distance = d[len(string1)][len(string2)]
    
    if normalize_output:
        return 1 - (distance / max(len(string1), len(string2)))
    else:
        return distance

def find_common_substring(string1, string2):
    """
    Find the longest common substring between two strings.
    """
    shorter = string1 if len(string1) <= len(string2) else string2
    longer = string2 if len(string1) <= len(string2) else string1
    
    for i in range(len(shorter), 0, -1):
        for j in range(len(shorter) - i + 1):
            substring = shorter[j:j+i]
            if substring in longer:
                return substring
    return ""

def domain_provided_route(users_list, provided_domains):
    """
    Process users with provided company domains.
    """
    results = []
    
    for user in users_list:
        # Extract user data
        user_id = user.get('id', 'N/A')
        signin_status = "Enabled" if user.get('allow_logon', False) else "Disabled"
        full_name = user.get('full_name', 'N/A')
        email = user.get('email', 'N/A')
        
        # Skip users with invalid emails
        if not email or '@' not in email:
            continue
            
        domain = email.split('@')[1]
        
        # Check if user's domain is in the provided company domains
        classification = "Internal" if domain in provided_domains else "External"
        
        # If external, prepare new email with .Ext suffix
        new_email = f"{email}.Ext" if classification == "External" else ""
        
        # Only include disabled users in results
        if signin_status == "Disabled":
            results.append({
                "UserID": user_id,
                "FullName": full_name,
                "Email": email,
                "NewEmail": new_email,
                "Domain": domain,
                "Classification": classification,
                "Status": signin_status
            })
    
    return results

def domain_discovery_route(users_list):
    """
    Process users by discovering the company domain.
    """
    # Create log directory if it doesn't exist
    log_dir = Path(__file__).parent / "Logs"
    if not log_dir.exists():
        log_dir.mkdir()
    
    log_file_path = log_dir / "classifyscriptlog.txt"
    
    # Log start of process
    with open(log_file_path, "a") as log_file:
        log_file.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Retrieving company email domains...\n")
    
    # Extract domains from emails
    domains = []
    for user in users_list:
        user_id = user.get('id', 'N/A')
        signin_status = "Enabled" if user.get('allow_logon', False) else "Disabled"
        full_name = user.get('full_name', 'N/A')
        email = user.get('email', 'N/A')
        
        # Skip users with invalid emails
        if not email or '@' not in email:
            continue
            
        domain = email.split('@')[1]
        root_domain = domain.split('.')[0]
        
        domains.append({
            "Email": email,
            "Domain": domain,
            "RootDomain": root_domain,
            "UserID": user_id,
            "Status": signin_status,
            "FullName": full_name
        })
    
    # Find the most common domain (assumed to be the company domain)
    domain_counts = {}
    for item in domains:
        domain = item["Domain"]
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    company_domain = max(domain_counts.items(), key=lambda x: x[1])[0] if domain_counts else ""
    
    # Log domain discovery
    with open(log_file_path, "a") as log_file:
        log_file.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
                      f"Classifying users as internal or external based on domain match with '{company_domain}' or similarity...\n")
    
    # Classify users
    results = []
    for item in domains:
        root_domain = item["RootDomain"].lower()
        main_root_domain = company_domain.split('.')[0].lower() if company_domain else ""
        
        # Find common substring
        common_substring = find_common_substring(main_root_domain, root_domain).lower()
        
        # Calculate closeness
        closeness = get_levenshtein_distance(main_root_domain, common_substring)
        
        # Calculate percentage closeness
        percent_closeness = round((len(main_root_domain) - closeness) / len(main_root_domain) * 100) if main_root_domain else 0
        
        # Determine if domains are similar
        similar = percent_closeness >= 50
        
        # Classify user
        classification = "Internal" if item["Domain"] == company_domain or similar else "External"
        
        # Prepare new email if external
        new_email = f"{item['Email']}.Ext" if classification == "External" else ""
        
        # Only include disabled users in results
        if item["Status"] == "Disabled":
            results.append({
                "UserID": item["UserID"],
                "FullName": item["FullName"],
                "Email": item["Email"],
                "NewEmail": new_email,
                "Domain": item["Domain"],
                "Classification": classification,
                "Status": item["Status"]
            })
    
    return results

class UserReportWidget(QWidget):
    """Widget that displays the user report table"""
    process_clicked = pyqtSignal()
    back_clicked = pyqtSignal()
    
    def __init__(self, users):
        super().__init__()
        self.users = users
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("User Report")
        header.setStyleSheet("font-size: 22px; font-weight: 600; color: #1E293B; padding-bottom: 5px;")
        layout.addWidget(header)
        
        # User count
        count_label = QLabel(f"Successfully retrieved {len(users)} users")
        count_label.setStyleSheet("font-size: 13px; color: #64748B; margin-bottom: 8px;")
        layout.addWidget(count_label)
        
        # Create a split layout
        split_widget = QWidget()
        split_layout = QHBoxLayout(split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(20)  # Add space between the panels
        
        # LEFT PANEL - User Table
        table_panel = QWidget()
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Table header
        table_header = QLabel("User Data")
        table_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #1E293B; margin-bottom: 10px;")
        table_layout.addWidget(table_header)
        
        # Table container
        table_container = QFrame()
        table_container.setFrameShape(QFrame.Shape.StyledPanel)
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
            }
        """)
        
        inner_table_layout = QVBoxLayout(table_container)
        inner_table_layout.setContentsMargins(10, 10, 10, 10)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["UserID", "Sign in Status", "Full Name", "Email"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #F1F5F9;
                color: #1E293B;
            }
            QTableWidget::item {
                padding: 4px;
                color: #1E293B;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                padding: 8px;
                font-weight: bold;
                color: #1E293B;
            }
        """)
        
        inner_table_layout.addWidget(self.table)
        table_layout.addWidget(table_container)
        
        # RIGHT PANEL - Sanitization Options
        options_panel = QWidget()
        options_layout = QVBoxLayout(options_panel)
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        # Options header
        options_header = QLabel("Email Sanitization Options")
        options_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #1E293B; margin-bottom: 10px;")
        options_layout.addWidget(options_header)
        
        # Options container with a clean white design
        options_container = QFrame()
        options_container.setFrameShape(QFrame.Shape.StyledPanel)
        options_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
            }
        """)
        
        options_inner_layout = QVBoxLayout(options_container)
        options_inner_layout.setContentsMargins(15, 15, 15, 15)
        options_inner_layout.setSpacing(20)  # Increase spacing between elements
        
        # Option description with better formatting
        option_desc = QLabel("This tool will identify external and internal users based on email domains.")
        option_desc.setWordWrap(True)
        option_desc.setStyleSheet("color: #475569; font-size: 14px;")
        options_inner_layout.addWidget(option_desc)
        
        # Selection method group with visually distinct options
        method_group = QFrame()
        method_group.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        
        method_layout = QVBoxLayout(method_group)
        method_layout.setContentsMargins(15, 15, 15, 15)
        method_layout.setSpacing(15)  # Good spacing between radio buttons
        
        # Method selector label
        method_label = QLabel("Select Domain Source:")
        method_label.setStyleSheet("font-weight: 600; color: #1E293B; font-size: 14px;")
        method_layout.addWidget(method_label)
        
        # Create option 1 with icon and better radio button
        option1_widget = QWidget()
        option1_layout = QHBoxLayout(option1_widget)
        option1_layout.setContentsMargins(0, 0, 0, 0)
        
        self.provide_domains_radio = QRadioButton()
        self.provide_domains_radio.setChecked(True)
        self.provide_domains_radio.setStyleSheet("""
            QRadioButton {
                spacing: 10px;
            }
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #CBD5E1;
                border-radius: 10px;
            }
            QRadioButton::indicator:checked {
                background-color: #3B82F6;
                border: 2px solid #3B82F6;
                width: 20px;
                height: 20px;
                border-radius: 10px;
            }
            QRadioButton::indicator:unchecked {
                background-color: white;
            }
        """)
        
        option1_icon = QLabel("🔤")
        option1_icon.setStyleSheet("font-size: 18px;")
        
        option1_text = QLabel("Provide company domains")
        option1_text.setStyleSheet("font-size: 14px; color: #1E293B;")
        
        option1_layout.addWidget(self.provide_domains_radio)
        option1_layout.addWidget(option1_icon)
        option1_layout.addWidget(option1_text, 1)  # 1 = stretch factor
        method_layout.addWidget(option1_widget)
        
        # Create option 2 with icon
        option2_widget = QWidget()
        option2_layout = QHBoxLayout(option2_widget)
        option2_layout.setContentsMargins(0, 0, 0, 0)
        
        self.discover_domains_radio = QRadioButton()
        self.discover_domains_radio.setStyleSheet("""
            QRadioButton {
                spacing: 10px;
            }
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #CBD5E1;
                border-radius: 10px;
            }
            QRadioButton::indicator:checked {
                background-color: #3B82F6;
                border: 2px solid #3B82F6;
                width: 20px;
                height: 20px;
                border-radius: 10px;
            }
            QRadioButton::indicator:unchecked {
                background-color: white;
            }
        """)
        
        option2_icon = QLabel("🔍")
        option2_icon.setStyleSheet("font-size: 18px;")
        
        option2_text = QLabel("Automatically discover domains")
        option2_text.setStyleSheet("font-size: 14px; color: #1E293B;")
        
        option2_layout.addWidget(self.discover_domains_radio)
        option2_layout.addWidget(option2_icon)
        option2_layout.addWidget(option2_text, 1)  # 1 = stretch factor
        method_layout.addWidget(option2_widget)
        
        options_inner_layout.addWidget(method_group)
        
        # Domain input with cleaner design
        self.domain_input_container = QFrame()
        self.domain_input_container.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        
        domain_input_layout = QVBoxLayout(self.domain_input_container)
        domain_input_layout.setContentsMargins(15, 15, 15, 15)
        
        domain_label = QLabel("Company Domains:")
        domain_label.setStyleSheet("font-weight: 600; color: #1E293B; font-size: 14px;")
        
        domain_help = QLabel("Enter company domains separated by commas")
        domain_help.setStyleSheet("color: #64748B; font-size: 12px; margin-bottom: 5px;")
        
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("example.com, company.org")
        self.domain_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background-color: white;
                color: #1E293B;
            }
            QLineEdit:focus {
                border: 2px solid #3B82F6;
            }
        """)
        self.domain_input.setMinimumHeight(40)
        
        domain_input_layout.addWidget(domain_label)
        domain_input_layout.addWidget(domain_help)
        domain_input_layout.addWidget(self.domain_input)
        
        options_inner_layout.addWidget(self.domain_input_container)
        
        # Connect radio buttons to toggle domain input visibility
        self.provide_domains_radio.toggled.connect(self.toggle_domain_input)
        
        # Add a helper text
        helper_text = QLabel("Only disabled users will be processed for sanitization")
        helper_text.setStyleSheet("color: #64748B; font-style: italic; font-size: 12px; margin-top: 10px;")
        
        options_inner_layout.addStretch()
        options_inner_layout.addWidget(helper_text)
        
        options_layout.addWidget(options_container)
        
        # Add both panels to the split layout with appropriate widths
        split_layout.addWidget(table_panel, 3)  # Table takes 3/5 of the width
        split_layout.addWidget(options_panel, 2)  # Options take 2/5 of the width
        
        # Add the split widget to the main layout
        layout.addWidget(split_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 16, 0, 0)
        
        self.back_btn = QPushButton("Back")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #475569;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #CBD5E1;
            }
        """)
        
        self.process_btn = QPushButton("Process Emails")
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        
        button_layout.addWidget(self.back_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.process_btn)
        
        layout.addLayout(button_layout)
        
        # Connect buttons
        self.back_btn.clicked.connect(self.back_clicked)
        self.process_btn.clicked.connect(self.process_clicked)
        
        # Populate table
        self.populate_table()
        
    def populate_table(self):
        self.table.setRowCount(len(self.users))
        for row, user in enumerate(self.users):
            if isinstance(user, str):
                # If user is just a string (email)
                id_item = QTableWidgetItem("N/A")
                status_item = QTableWidgetItem("N/A")
                name_item = QTableWidgetItem("N/A")
                email_item = QTableWidgetItem(user)
                
                # Set text color to ensure visibility
                id_item.setForeground(QColor("#1E293B"))
                status_item.setForeground(QColor("#1E293B"))
                name_item.setForeground(QColor("#1E293B"))
                email_item.setForeground(QColor("#1E293B"))
                
                self.table.setItem(row, 0, id_item)
                self.table.setItem(row, 1, status_item)
                self.table.setItem(row, 2, name_item)
                self.table.setItem(row, 3, email_item)
            else:
                # Extract user fields
                user_id = user.get('id', 'N/A')
                allow_logon = "Enabled" if user.get('allow_logon', False) else "Disabled"
                full_name = user.get('full_name', 'N/A')
                email = user.get('email', 'N/A')
                
                # Set table items with explicit colors
                id_item = QTableWidgetItem(user_id)
                id_item.setForeground(QColor("#1E293B"))
                
                status_item = QTableWidgetItem(allow_logon)
                if allow_logon == "Disabled":
                    status_item.setForeground(QColor("#DC2626"))  # Red text for disabled
                else:
                    status_item.setForeground(QColor("#059669"))  # Green text for enabled
                
                name_item = QTableWidgetItem(full_name)
                name_item.setForeground(QColor("#1E293B"))
                
                email_item = QTableWidgetItem(email)
                email_item.setForeground(QColor("#1E293B"))
                
                self.table.setItem(row, 0, id_item)
                self.table.setItem(row, 1, status_item)
                self.table.setItem(row, 2, name_item)
                self.table.setItem(row, 3, email_item)
    
    def toggle_domain_input(self, checked):
        self.domain_input_container.setVisible(checked)
        
    def get_selected_option(self):
        if self.provide_domains_radio.isChecked():
            domains_input = self.domain_input.text().strip()
            provided_domains = [d.strip() for d in domains_input.split(',') if d.strip()]
            return "provided", provided_domains
        else:
            return "discovery", None

class ResultsWidget(QWidget):
    """Widget that displays the email sanitization results"""
    back_clicked = pyqtSignal()
    
    def __init__(self, results):
        super().__init__()
        self.results = results
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Sanitization Results (Disabled Users Only)")
        header.setStyleSheet("font-size: 22px; font-weight: 600; color: #1E293B; padding-bottom: 5px;")
        layout.addWidget(header)
        
        # Results count
        count_label = QLabel(f"Found {len(results)} disabled user(s) that need attention.")
        count_label.setStyleSheet("font-size: 13px; color: #64748B; margin-bottom: 10px;")
        layout.addWidget(count_label)
        
        # Table container
        table_container = QFrame()
        table_container.setFrameShape(QFrame.Shape.StyledPanel)
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
            }
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["UserID", "Full Name", "Email", "Classification", "New Email (if External)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #F1F5F9;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                padding: 4px;
                font-weight: bold;
                color: #1E293B;
            }
        """)
        table_layout.addWidget(self.table)
        
        # Add table container to layout
        layout.addWidget(table_container)
        
        # Populate table
        self.populate_table()
        
        # Button
        button_layout = QHBoxLayout()
        self.back_btn = QPushButton("Back to Email Tools")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.back_btn)
        
        layout.addLayout(button_layout)
        
        # Connect button
        self.back_btn.clicked.connect(self.back_clicked)
    
    def populate_table(self):
        self.table.setRowCount(len(self.results))
        for row, result in enumerate(self.results):
            # Set table items
            self.table.setItem(row, 0, QTableWidgetItem(result["UserID"]))
            self.table.setItem(row, 1, QTableWidgetItem(result["FullName"]))
            self.table.setItem(row, 2, QTableWidgetItem(result["Email"]))
            
            # Classification column
            classification_item = QTableWidgetItem(result["Classification"])
            if result["Classification"] == "External":
                classification_item.setForeground(QColor("#D97706"))  # Amber text
                classification_item.setIcon(QIcon("./ui/assets/external_icon.png"))  # Optional icon
            else:
                classification_item.setForeground(QColor("#059669"))  # Green text
                classification_item.setIcon(QIcon("./ui/assets/internal_icon.png"))  # Optional icon
            
            self.table.setItem(row, 3, classification_item)
            
            # New email column with conditional formatting
            email_item = QTableWidgetItem(result["NewEmail"])
            if result["NewEmail"]:
                email_item.setForeground(QColor("#059669"))  # Green text
            
            self.table.setItem(row, 4, email_item)

class EmailSanitizerPage(QWidget):
    """Main widget for the email sanitizer functionality"""
    back_to_tools_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.users = []
        
        # Main layout with proper margins for clean appearance
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 16, 25, 20)
        main_layout.setSpacing(12)

        # Header with status
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Email Sanitizer")
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
        """)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 4px;
            background: #F1F5F9;
            color: #64748B;
        """)
        
        header_layout.addWidget(header)
        header_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch()
        
        main_layout.addWidget(header_container)
        
        # Stacked widget to manage different views
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Create the main configuration panel
        self.sanitizer_panel = self.create_sanitizer_panel()
        self.progress_widget = self.create_progress_widget()
        self.results_widget = self.create_results_widget()
        self.user_table_widget = self.create_user_table_widget()
        
        # Add widgets to stack
        self.stack.addWidget(self.sanitizer_panel)
        self.stack.addWidget(self.progress_widget)
        self.stack.addWidget(self.results_widget)
        self.stack.addWidget(self.user_table_widget)
        
        # Show sanitizer panel by default
        self.stack.setCurrentWidget(self.sanitizer_panel)
    
    def create_sanitizer_panel(self):
        """Create the main sanitizer configuration panel, modeled after the account settings page"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Form container
        form = QFrame()
        # Remove fixed width to allow proper scaling with window size
        form.setMinimumWidth(580)
        form.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
                border-radius: 10px;
            }
        """)
        
        form_layout = QVBoxLayout(form)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(20, 16, 20, 16)
        
        # Description text with word wrap explicitly enabled
        description = QLabel("This tool identifies external and internal users by analyzing email domains, "
                            "and helps sanitize email addresses for disabled accounts.")
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: #475569;
            font-size: 14px;
            margin-bottom: 10px;
        """)
        content_layout.addWidget(description)
        
        # Domain selection section - ensure text wraps properly
        domain_section_label = QLabel("Domain Source")
        domain_section_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #0F172A;
            margin-top: 8px;
        """)
        content_layout.addWidget(domain_section_label)
        
        # Radio buttons in clean layout with improved text handling
        radio_container = QWidget()
        radio_container.setStyleSheet("""
            background-color: #F8FAFC;
            border-radius: 8px;
            padding: 4px;
        """)
        radio_layout = QVBoxLayout(radio_container)
        radio_layout.setContentsMargins(16, 12, 16, 12)
        radio_layout.setSpacing(12)
        
        # Option 1 with better text wrapping
        self.provide_domains_radio = QRadioButton("Provide company domains manually")
        self.provide_domains_radio.setChecked(True)
        self.provide_domains_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                color: #1E293B;
                padding: 4px 0;
                min-height: 24px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        
        # Option 2 with better text wrapping
        self.discover_domains_radio = QRadioButton("Automatically discover domains from user data")
        self.discover_domains_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                color: #1E293B;
                padding: 4px 0;
                min-height: 24px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        
        radio_layout.addWidget(self.provide_domains_radio)
        radio_layout.addWidget(self.discover_domains_radio)
        
        content_layout.addWidget(radio_container)
        
        # Domain input section - INCREASED WIDTH for better text visibility
        domain_input_container = QWidget()
        domain_input_layout = QGridLayout(domain_input_container)
        domain_input_layout.setContentsMargins(0, 8, 0, 0)
        domain_input_layout.setVerticalSpacing(8)
        domain_input_layout.setHorizontalSpacing(12)
        
        # Domain label with increased width
        domain_label = QLabel("Company Domains:")
        domain_label.setFixedWidth(130)  # Increased from 110 to 130
        domain_label.setStyleSheet("""
            font-size: 14px;
            color: #475569;
        """)
        
        # Domain input field
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("example.com, company.org")
        self.domain_input.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #E2E8F0;
                border-radius: 5px;
                padding: 8px 12px;
                background: white;
                color: #0F172A;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3B82F6;
            }
        """)
        
        # Help text
        help_text = QLabel("Enter multiple domains separated by commas")
        help_text.setStyleSheet("""
            font-size: 12px;
            color: #64748B;
            font-style: italic;
        """)
        
        domain_input_layout.addWidget(domain_label, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        domain_input_layout.addWidget(self.domain_input, 0, 1)
        domain_input_layout.addWidget(help_text, 1, 1)
        
        # Add domain input section to layout
        self.domain_input_section = domain_input_container
        content_layout.addWidget(domain_input_container)
        
        # Additional info
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 16, 0, 8)
        
        info_text = QLabel("Note: Only disabled users will be processed for email sanitization.")
        info_text.setStyleSheet("""
            color: #64748B;
            font-style: italic;
            font-size: 13px;
        """)
        
        info_layout.addWidget(info_text)
        content_layout.addWidget(info_container)
        
        # Connect radio buttons
        self.provide_domains_radio.toggled.connect(self.toggle_domain_input)
        
        # Add content to form
        form_layout.addWidget(content)
        
        # Bottom action panel
        action_panel = QWidget()
        action_panel.setStyleSheet("""
            QWidget {
                background: #F8FAFC;
                border-top: 1px solid #E2E8F0;
            }
        """)
        action_layout = QHBoxLayout(action_panel)
        action_layout.setContentsMargins(24, 20, 24, 20)
        
        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedSize(100, 38)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet("""
            QPushButton {
                color: #475569;
                border: 1.5px solid #CBD5E1;
                border-radius: 6px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #F1F5F9;
            }
        """)
        
        self.view_users_btn = QPushButton("View Users")
        self.view_users_btn.setFixedSize(120, 38)
        self.view_users_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_users_btn.setStyleSheet("""
            QPushButton {
                color: #3B82F6;
                border: 1.5px solid #3B82F6;
                border-radius: 6px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #EFF6FF;
            }
        """)
        
        self.process_btn = QPushButton("Process Emails")
        self.process_btn.setFixedSize(140, 38)
        self.process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2563EB;
            }
        """)
        
        action_layout.addWidget(self.back_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.view_users_btn)
        action_layout.addWidget(self.process_btn)
        
        # Connect buttons
        self.back_btn.clicked.connect(self.back_to_tools_clicked)
        self.view_users_btn.clicked.connect(self.show_user_table)
        self.process_btn.clicked.connect(self.process_emails)
        
        form_layout.addWidget(action_panel)
        
        # Add form to panel layout
        layout.addWidget(form, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        
        return panel
    
    # Replace the create_panel method with a simpler version
    def create_panel(self, title, fields):
        """Create a panel with fields, styled like account page panels"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 16)
        
        # Title at the top
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #0F172A; margin-bottom: 4px;")
        layout.addWidget(title_label)
        
        return panel
    
    def toggle_domain_input(self, checked):
        """Toggle visibility of domain input section based on radio selection"""
        self.domain_input_section.setVisible(checked)
        
    def create_progress_widget(self):
        """Create the progress indicator widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Progress frame
        progress_frame = QFrame()
        progress_frame.setFixedWidth(580)
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)
        
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(30, 40, 30, 40)
        progress_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress title
        progress_title = QLabel("Processing")
        progress_title.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #1E293B;
            margin-bottom: 10px;
        """)
        progress_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress description
        self.progress_label = QLabel("Analyzing and sanitizing email addresses...")
        self.progress_label.setStyleSheet("""
            font-size: 14px;
            color: #64748B;
            margin-bottom: 20px;
        """)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setFixedSize(400, 8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #F1F5F9;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 4px;
            }
        """)
        
        progress_layout.addWidget(progress_title)
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Back button container
        button_container = QWidget()
        button_container.setStyleSheet("""
            background: #F8FAFC;
            border-top: 1px solid #E2E8F0;
        """)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(24, 20, 24, 20)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 38)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                color: #475569;
                border: 1.5px solid #CBD5E1;
                border-radius: 6px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #F1F5F9;
            }
        """)
        cancel_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.sanitizer_panel))
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        
        progress_layout.addWidget(button_container)
        
        layout.addWidget(progress_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        
        return widget
    
    def create_results_widget(self):
        """Create the results display widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Results frame
        results_frame = QFrame()
        results_frame.setFixedWidth(580)
        results_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)
        
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        results_title = QLabel("Sanitization Results")
        results_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #0F172A;")
        
        self.results_count = QLabel()
        self.results_count.setStyleSheet("font-size: 13px; color: #64748B; margin-top: 4px;")
        
        header_layout.addWidget(results_title)
        header_layout.addWidget(self.results_count)
        
        # Table
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(20, 0, 20, 20)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["UserID", "Full Name", "Email", "Classification", "New Email"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                gridline-color: #F1F5F9;
                color: #1E293B;
            }
            QTableWidget::item {
                padding: 6px;
                color: #1E293B;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                padding: 6px;
                font-weight: bold;
                color: #1E293B;
            }
        """)
        
        table_layout.addWidget(self.results_table)
        
        # Action panel
        action_panel = QWidget()
        action_panel.setStyleSheet("""
            background: #F8FAFC;
            border-top: 1px solid #E2E8F0;
        """)
        
        action_layout = QHBoxLayout(action_panel)
        action_layout.setContentsMargins(24, 20, 24, 20)
        
        back_to_options_btn = QPushButton("Back to Options")
        back_to_options_btn.setFixedSize(140, 38)
        back_to_options_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_to_options_btn.setStyleSheet("""
            QPushButton {
                color: #475569;
                border: 1.5px solid #CBD5E1;
                border-radius: 6px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #F1F5F9;
            }
        """)
        back_to_options_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.sanitizer_panel))
        
        action_layout.addWidget(back_to_options_btn)
        action_layout.addStretch()
        
        # Add all components
        results_layout.addWidget(header)
        results_layout.addWidget(table_container)
        results_layout.addWidget(action_panel)
        
        layout.addWidget(results_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        
        return widget

    def create_user_table_widget(self):
        """Create the user table display widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # User table frame - no fixed width, use minimum width instead
        table_frame = QFrame()
        table_frame.setMinimumWidth(900)
        table_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)
        
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        # Header with cleaner style
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        users_title = QLabel("User Report")
        users_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #0F172A;")
        
        self.user_count = QLabel()
        self.user_count.setStyleSheet("font-size: 13px; color: #64748B; margin-top: 4px;")
        
        header_layout.addWidget(users_title)
        header_layout.addWidget(self.user_count)
        
        # Table container with improved styling and vertical stretch
        table_container = QWidget()
        table_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table_layout_container = QVBoxLayout(table_container)
        table_layout_container.setContentsMargins(16, 0, 16, 16)
        
        self.user_table = QTableWidget()
        self.user_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.user_table.setMinimumHeight(400)  # Enforce minimum height
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["UserID", "Sign in Status", "Full Name", "Email"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.user_table.horizontalHeader().setMinimumHeight(40)
        self.user_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                gridline-color: #E2E8F0;
                color: #1E293B;
                background-color: white;
                alternate-background-color: #F8FAFC;
                selection-background-color: #EFF6FF;
                selection-color: #1E293B;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F1F5F9;
            }
            QTableWidget::item:selected {
                background-color: #EFF6FF;
            }
            QHeaderView::section {
                background-color: #F1F5F9;
                border: 1px solid #E2E8F0;
                padding: 8px;
                font-weight: 600;
                color: #0F172A;
                font-size: 13px;
            }
        """)
        
        # Enhanced table appearance
        self.user_table.setShowGrid(True)
        self.user_table.setAlternatingRowColors(True)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        table_layout_container.addWidget(self.user_table)
        
        # Action panel with consistent style
        action_panel = QWidget()
        action_panel.setStyleSheet("""
            background: #F8FAFC;
            border-top: 1px solid #E2E8F0;
        """)
        
        action_layout = QHBoxLayout(action_panel)
        action_layout.setContentsMargins(24, 20, 24, 20)
        
        back_to_options_btn = QPushButton("Back to Options")
        back_to_options_btn.setFixedSize(140, 38)
        back_to_options_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_to_options_btn.setStyleSheet("""
            QPushButton {
                color: #475569;
                border: 1.5px solid #CBD5E1;
                border-radius: 6px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #F1F5F9;
            }
        """)
        back_to_options_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.sanitizer_panel))
        
        action_layout.addWidget(back_to_options_btn)
        action_layout.addStretch()
        
        # Add all components
        table_layout.addWidget(header)
        table_layout.addWidget(table_container)
        table_layout.addWidget(action_panel)
        
        layout.addWidget(table_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        
        return widget
    
    def toggle_domain_panel(self, checked):
        """Toggle visibility of domain input panel based on radio selection"""
        self.domains_panel.setVisible(checked)
    
    def show_user_table(self):
        """Show the user table view"""
        self.stack.setCurrentWidget(self.user_table_widget)
    
    def process_emails(self):
        """Process emails based on selected options"""
        # Update UI
        self.stack.setCurrentWidget(self.progress_widget)
        self.status_label.setText("Processing...")
        QApplication.processEvents()
        
        try:
            # Get selected option
            if self.provide_domains_radio.isChecked():
                domains_input = self.domain_input.text().strip()
                provided_domains = [d.strip() for d in domains_input.split(',') if d.strip()]
                
                if not provided_domains:
                    QMessageBox.warning(self, "Input Error", "Please enter at least one domain.")
                    self.stack.setCurrentWidget(self.sanitizer_panel)
                    self.status_label.setText("Ready")
                    return
                
                results = domain_provided_route(self.users, provided_domains)
            else:
                results = domain_discovery_route(self.users)
            
            # Show results
            if results:
                self.display_results(results)
            else:
                QMessageBox.information(self, "No Results", "No disabled users found that need email sanitization.")
                self.stack.setCurrentWidget(self.sanitizer_panel)
                self.status_label.setText("No Results Found")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error processing emails: {str(e)}")
            self.stack.setCurrentWidget(self.sanitizer_panel)
            self.status_label.setText("Error")
    
    def load_data(self, users):
        """Load user data and update UI"""
        self.users = users
        self.populate_user_table()
        self.user_count.setText(f"Found {len(users)} users")
        self.status_label.setText(f"{len(users)} Users Loaded")
    
    def populate_user_table(self):
        """Populate the user table with data"""
        self.user_table.setRowCount(len(self.users))
        
        # Calculate appropriate row height based on available space
        available_height = self.user_table.height() - self.user_table.horizontalHeader().height()
        row_height = max(40, min(60, available_height / max(len(self.users), 1)))
        
        for row, user in enumerate(self.users):
            if isinstance(user, str):
                # If user is just a string (email)
                id_item = QTableWidgetItem("N/A")
                status_item = QTableWidgetItem("N/A")
                name_item = QTableWidgetItem("N/A")
                email_item = QTableWidgetItem(user)
                
                # Clear styling without custom backgrounds that can conflict with alternating rows
                id_item.setForeground(QColor("#1E293B"))
                status_item.setForeground(QColor("#1E293B"))
                name_item.setForeground(QColor("#1E293B"))
                email_item.setForeground(QColor("#1E293B"))
                
                self.user_table.setItem(row, 0, id_item)
                self.user_table.setItem(row, 1, status_item)
                self.user_table.setItem(row, 2, name_item)
                self.user_table.setItem(row, 3, email_item)
            else:
                # Extract user fields
                user_id = user.get('id', 'N/A')
                allow_logon = "Enabled" if user.get('allow_logon', False) else "Disabled"
                full_name = user.get('full_name', 'N/A')
                email = user.get('email', 'N/A')
                
                # Create table items with just text color styling
                id_item = QTableWidgetItem(user_id)
                id_item.setForeground(QColor("#1E293B"))
                
                status_item = QTableWidgetItem(allow_logon)
                if allow_logon == "Disabled":
                    status_item.setForeground(QColor("#DC2626"))  # Bright red for disabled
                else:
                    status_item.setForeground(QColor("#059669"))  # Green for enabled
                
                name_item = QTableWidgetItem(full_name)
                name_item.setForeground(QColor("#1E293B"))
                
                email_item = QTableWidgetItem(email)
                email_item.setForeground(QColor("#1E293B"))
                
                self.user_table.setItem(row, 0, id_item)
                self.user_table.setItem(row, 1, status_item)
                self.user_table.setItem(row, 2, name_item)
                self.user_table.setItem(row, 3, email_item)
                
        # Apply consistent row heights with calculated value
        for i in range(len(self.users)):
            self.user_table.setRowHeight(i, int(row_height))
        
        # Resize columns to content first, then apply stretching
        self.user_table.resizeColumnsToContents()
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Ensure table expands to fill available space
        self.user_table.updateGeometry()
    
    def display_results(self, results):
        """Display results in the results table"""
        self.results_table.setRowCount(len(results))
        for row, result in enumerate(results):
            # Set table items
            self.results_table.setItem(row, 0, QTableWidgetItem(result["UserID"]))
            self.results_table.setItem(row, 1, QTableWidgetItem(result["FullName"]))
            self.results_table.setItem(row, 2, QTableWidgetItem(result["Email"]))
            
            # Classification column
            classification_item = QTableWidgetItem(result["Classification"])
            if result["Classification"] == "External":
                classification_item.setForeground(QColor("#D97706"))  # Amber for external
            else:
                classification_item.setForeground(QColor("#059669"))  # Green for internal
            
            self.results_table.setItem(row, 3, classification_item)
            
            # New email column
            email_item = QTableWidgetItem(result["NewEmail"])
            if result["NewEmail"]:
                email_item.setForeground(QColor("#059669"))  # Green for new email
            
            self.results_table.setItem(row, 4, email_item)
        
        # Update UI
        self.results_count.setText(f"Found {len(results)} users that need email sanitization")
        self.stack.setCurrentWidget(self.results_widget)
        self.status_label.setText(f"{len(results)} Results Found")

def sanitize_emails():
    """Sanitizes user emails by checking domains and updating as needed"""
    # Read the user list from temp file
    temp_path = Path(__file__).parent.parent / 'temp_users.json'
    if not temp_path.exists():
        QMessageBox.critical(None, "Error", "No user list found. Make sure you're logged in and have proper permissions.")
        return None

    try:
        with open(temp_path) as f:
            users = json.load(f)
            
        if not users:
            QMessageBox.warning(None, "Warning", "No users found in the system")
            return None
        
        return users
            
    except json.JSONDecodeError:
        QMessageBox.critical(None, "Error", "Invalid JSON data in user list")
        return None
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error processing users: {str(e)}")
        return None
        
if __name__ == '__main__':
    # For standalone testing
    import sys
    app = QApplication(sys.argv)
    
    # Test with dummy data
    dummy_users = [
        {"id": "user1", "allow_logon": True, "full_name": "User One", "email": "user1@internal.com"},
        {"id": "user2", "allow_logon": False, "full_name": "User Two", "email": "user2@external.com"}
    ]
    
    page = EmailSanitizerPage()
    page.load_data(dummy_users)
    page.show()
    
    sys.exit(app.exec())