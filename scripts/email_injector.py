from pathlib import Path
import json
import random
from PyQt6.QtWidgets import QMessageBox
from ui.utils import log_function_execution

def inject_emails():
    """Injects placeholder emails for users that don't have an email set"""
    try:
        log_function_execution("email_injector", "STARTED", {
            "description": "Starting email injection process"
        })
        
        # Read the user list from temp file
        temp_path = Path(__file__).parent.parent / 'temp_users.json'
        if not temp_path.exists():
            error_msg = "No user list found. Make sure you're logged in and have proper permissions."
            log_function_execution("email_injector", "FAILED", {
                "error": error_msg
            })
            QMessageBox.critical(None, "Error", error_msg)
            return False
            
        # Load users
        with open(temp_path) as f:
            users = json.load(f)
            
        if not users:
            error_msg = "No users found in the system"
            log_function_execution("email_injector", "FAILED", {
                "error": error_msg,
                "users_count": 0
            })
            QMessageBox.warning(None, "Warning", error_msg)
            return False
            
        # Domains for placeholder emails
        domains = [
            "example.com", "placeholder.net", "placeholder.org", 
            "mail.example.org", "tempmail.com"
        ]
        
        modified_count = 0
        total_users = len(users)
        
        # Process each user
        for user in users:
            # Skip users that already have an email
            if user.get('email') and '@' in user.get('email', ''):
                continue
                
            # Generate a placeholder email
            username = user.get('username', '').lower() or f"user{random.randint(1000, 9999)}"
            domain = random.choice(domains)
            placeholder_email = f"{username}@{domain}"
            
            # Update the user's email
            user['email'] = placeholder_email
            modified_count += 1
            
        # Save changes
        with open(temp_path, 'w') as f:
            json.dump(users, f, indent=2)
            
        success_msg = f"Email injection completed. Modified {modified_count} of {total_users} user records."
        log_function_execution("email_injector", "SUCCESS", {
            "modified_count": modified_count,
            "total_users": total_users
        })
        
        QMessageBox.information(None, "Success", success_msg)
        return True
        
    except Exception as e:
        error_msg = f"Error during email injection: {str(e)}"
        log_function_execution("email_injector", "FAILED", {
            "error": error_msg
        })
        QMessageBox.critical(None, "Error", error_msg)
        return False

if __name__ == "__main__":
    inject_emails()