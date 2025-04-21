import os
import datetime
from pathlib import Path

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