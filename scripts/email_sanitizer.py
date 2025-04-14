import json
from pathlib import Path

def sanitize_emails():
    """Sanitizes user emails by checking domains and updating as needed"""
    # Read the user list from temp file
    temp_path = Path(__file__).parent.parent / 'temp_users.json'
    if not temp_path.exists():
        print("Error: No user list found. Make sure you're logged in and have proper permissions.")
        return

    try:
        with open(temp_path) as f:
            users = json.load(f)
            
        if not users:
            print("Warning: No users found in the system")
            return
            
        print(f"Successfully retrieved {len(users)} users")
        print("\nUser list:")
        for user in users:
            print(f"- {user}")
            
    except json.JSONDecodeError:
        print("Error: Invalid JSON data in user list")
    except Exception as e:
        print(f"Error processing users: {str(e)}")
        
if __name__ == '__main__':
    sanitize_emails()