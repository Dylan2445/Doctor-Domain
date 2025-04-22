import os
import datetime
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QPushButton

# Ensure the logs directory exists
LOG_DIR = Path(__file__).parent.parent / "scripts" / "Logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Main system log file
SYSTEM_LOG_FILE = LOG_DIR / "system_log.txt"

def log_message(message, log_file=SYSTEM_LOG_FILE):
    """
    Write a timestamped message to the specified log file.
    
    Args:
        message (str): Message to log
        log_file (Path, optional): Path to log file. Defaults to system log.
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create the parent directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - {message}\n")

def log_function_execution(function_name, status, details=None):
    """
    Log the execution of a function with status and optional details.
    
    Args:
        function_name (str): Name of the function being executed
        status (str): Success or failure status
        details (dict, optional): Additional details like URLs, status codes, etc.
    """
    message = f"Function {function_name}: {status}"
    
    if details:
        # Format details with special handling for URLs and status codes
        detail_parts = []
        for k, v in details.items():
            if k.lower() == 'url':
                detail_parts.append(f"URL: {v}")
            elif k.lower() == 'status_code':
                detail_parts.append(f"Status: {v}")
            else:
                detail_parts.append(f"{k}: {v}")
        
        if detail_parts:
            message += f" - {', '.join(detail_parts)}"
    
    log_message(message)

def create_styled_message_box(parent=None, title="", text="", icon=QMessageBox.Icon.Information, 
                             buttons=QMessageBox.StandardButton.Ok, default_button=None):
    """
    Create a styled QMessageBox with properly visible buttons.
    
    Args:
        parent: Parent widget
        title (str): Window title
        text (str): Message text
        icon: QMessageBox icon (default: Information)
        buttons: StandardButtons to display (default: Ok)
        default_button: Default button (default: None - first button)
    
    Returns:
        QMessageBox: Styled message box ready to show
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setIcon(icon)
    msg_box.setStandardButtons(buttons)
    
    if default_button:
        msg_box.setDefaultButton(default_button)
    
    # Apply universal styling that doesn't rely on button text selectors
    # This ensures buttons are visible in all environments
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: white;
        }
        QMessageBox QLabel {
            color: #1E293B;
            font-size: 14px;
            padding: 10px;
        }
        QMessageBox QPushButton {
            min-width: 80px;
            min-height: 30px;
            padding: 6px 14px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
            background-color: #F1F5F9;
            color: #1E293B;
            border: 1px solid #CBD5E1;
        }
        QMessageBox QPushButton:hover {
            background-color: #E2E8F0;
        }
    """)
    
    # Get all buttons and style them individually based on their role
    # This approach doesn't rely on text attributes which can be unreliable
    buttons = msg_box.findChildren(QPushButton)
    for button in buttons:
        if msg_box.buttonRole(button) == QMessageBox.ButtonRole.AcceptRole or \
           msg_box.buttonRole(button) == QMessageBox.ButtonRole.YesRole:
            button.setStyleSheet("""
                background-color: #3B82F6;
                color: white;
                border: 1px solid #2563EB;
                min-width: 80px;
                min-height: 30px;
                padding: 6px 14px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            """)
        elif msg_box.buttonRole(button) == QMessageBox.ButtonRole.RejectRole or \
             msg_box.buttonRole(button) == QMessageBox.ButtonRole.NoRole:
            button.setStyleSheet("""
                background-color: #E2E8F0;
                color: #475569;
                border: 1px solid #CBD5E1;
                min-width: 80px;
                min-height: 30px;
                padding: 6px 14px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            """)
    
    return msg_box