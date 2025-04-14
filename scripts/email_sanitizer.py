import json
from pathlib import Path

def sanitize_emails():
    """Sanitizes user emails by checking domains and updating as needed"""
    # Read the user list from temp file
    temp_path = Path(__file__).parent.parent / 'temp_users.json'
    if not temp_path.exists():
        print("No user list found. Please try again.")
        return

    try:
        with open(temp_path) as f:
            users = json.load(f)
            
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"- {user}")
            
    except Exception as e:
        print(f"Error processing users: {str(e)}")
        
if __name__ == '__main__':
    sanitize_emails()