from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit, 
                           QHBoxLayout, QPushButton, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from pathlib import Path
import datetime
import os
import glob
import hashlib

class LogsPage(QWidget):
    """Page that displays logs from various operations"""
    
    def __init__(self):
        super().__init__()
        self.log_dir = Path(__file__).parent.parent.parent / "scripts" / "Logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Consolidated log file
        self.log_file = self.log_dir / "consolidated_log.txt"
        
        # Store hashes of log entries to avoid duplicates
        self.log_entry_hashes = set()
        self.last_file_modified_times = {}
        self.is_first_load = True
        
        # Create timer for auto-refresh with a longer interval
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_log)
        self.update_timer.setInterval(10000)  # Refresh every 10 seconds instead of 2
        
        self.setup_ui()
        self.consolidate_logs(force=True)  # Combine existing logs initially
        self.refresh_log()
        self.update_timer.start()
        
        # Reference to main window (will be set by main application)
        self.main_window = None
        
    def set_main_window(self, main_window):
        """Set reference to main window for accessing global functionality"""
        self.main_window = main_window
        
        # Update toggle button state to match the overlay visibility
        self.update_overlay_toggle_state()
        
        # Connect the toggle button to the main window's toggle function
        self.overlay_toggle_btn.clicked.connect(self.toggle_overlay)
        
    def toggle_overlay(self):
        """Toggle the log overlay visibility using main window's function"""
        if self.main_window:
            self.main_window.toggle_log_overlay()
            self.update_overlay_toggle_state()
            
    def update_overlay_toggle_state(self):
        """Update the toggle button state to match the overlay visibility"""
        if self.main_window and hasattr(self.main_window, 'log_overlay'):
            is_visible = self.main_window.log_overlay.isVisible()
            self.overlay_toggle_btn.setChecked(is_visible)
            self.overlay_toggle_btn.setText("Hide Overlay" if is_visible else "Show Overlay")
    
    def setup_ui(self):
        # Main layout with proper margins for clean appearance
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 16, 25, 20)
        main_layout.setSpacing(12)

        # Header with status
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("System Logs")
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
        """)
        
        self.status_label = QLabel("Idle")
        self.status_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 4px;
            background: #F1F5F9;
            color: #64748B;
        """)
        
        # Auto refresh toggle
        self.auto_refresh_btn = QPushButton("Auto Refresh: ON")
        self.auto_refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setChecked(True)
        self.auto_refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #ECFDF5;
                color: #059669;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:checked {
                background-color: #ECFDF5;
                color: #059669;
            }
            QPushButton:!checked {
                background-color: #FEF2F2;
                color: #DC2626;
            }
        """)
        self.auto_refresh_btn.toggled.connect(self.toggle_auto_refresh)
        
        # Log overlay toggle button
        self.overlay_toggle_btn = QPushButton("Show Overlay")
        self.overlay_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.overlay_toggle_btn.setCheckable(True)
        self.overlay_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #EFF6FF;
                color: #3B82F6;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 500;
                margin-left: 6px;
            }
            QPushButton:checked {
                background-color: #DBEAFE;
                color: #2563EB;
            }
        """)
        
        header_layout.addWidget(header)
        header_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch()
        header_layout.addWidget(self.auto_refresh_btn)
        header_layout.addWidget(self.overlay_toggle_btn)
        
        main_layout.addWidget(header_container)
        
        # Log content panel
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
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Log content
        self.log_content = QTextEdit()
        self.log_content.setReadOnly(True)
        self.log_content.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: #FCFCFC;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                color: #1E293B;
                padding: 12px;
            }
        """)
        
        content_layout.addWidget(self.log_content)
        
        # Bottom action panel
        action_panel = QWidget()
        action_panel.setStyleSheet("""
            background-color: #F8FAFC;
            border-top: 1px solid #E2E8F0;
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
        """)
        action_layout = QHBoxLayout(action_panel)
        action_layout.setContentsMargins(16, 12, 16, 12)
        
        self.clear_btn = QPushButton("Clear Logs")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #DC2626;
                border: 1px solid #DC2626;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #FEF2F2;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_logs)
        
        self.manual_refresh_btn = QPushButton("Refresh Now")
        self.manual_refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manual_refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #EFF6FF;
                color: #3B82F6;
                border: 1px solid #DBEAFE;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #DBEAFE;
            }
        """)
        self.manual_refresh_btn.clicked.connect(self.refresh_log)
        
        action_layout.addWidget(self.clear_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.manual_refresh_btn)
        
        content_layout.addWidget(action_panel)
        
        # Add panel to main layout
        main_layout.addWidget(content_panel)
    
    def get_hash(self, text):
        """Create a hash for the log entry to detect duplicates"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def should_process_file(self, file_path):
        """Check if a file has been modified since last check"""
        if self.is_first_load:
            return True
            
        try:
            current_mtime = file_path.stat().st_mtime
            last_mtime = self.last_file_modified_times.get(str(file_path), 0)
            
            if current_mtime > last_mtime:
                self.last_file_modified_times[str(file_path)] = current_mtime
                return True
            return False
        except Exception:
            # If there's any error, process the file to be safe
            return True
    
    def consolidate_logs(self, force=False):
        """Combine all existing log files into a single consolidated log file"""
        # Get all log files except our consolidated one
        log_files = [f for f in self.log_dir.glob("*.txt") if f.name != "consolidated_log.txt"]
        
        # Read existing consolidated log if it exists
        consolidated_entries = []
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                    # Only process if there's content
                    if existing_content.strip():
                        for line in existing_content.splitlines():
                            line = line.strip()
                            if line:
                                # Add to hash set to avoid duplicates
                                entry_hash = self.get_hash(line)
                                self.log_entry_hashes.add(entry_hash)
                                consolidated_entries.append(line)
            except Exception:
                # If there's any error reading the file, continue with empty entries
                pass
        
        # Flag to track if we added any new entries
        new_entries_added = False
        
        # Process each log file
        for log_file in log_files:
            # Skip files that haven't changed
            if not force and not self.should_process_file(log_file):
                continue
                
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    # Skip empty files
                    if not file_content.strip():
                        continue
                    
                    # Process each line
                    for line in file_content.splitlines():
                        line = line.strip()
                        # Only add non-empty lines
                        if line:
                            # Check if line already has a timestamp
                            if line[:19].count('-') == 2 and line[:19].count(':') == 2:
                                # Line already has timestamp, don't add source marker
                                full_entry = line
                            else:
                                # Add current timestamp if missing
                                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                full_entry = f"{timestamp} - {line}"
                            
                            # Check if we've seen this entry before using the hash
                            entry_hash = self.get_hash(full_entry)
                            if entry_hash not in self.log_entry_hashes:
                                consolidated_entries.append(full_entry)
                                self.log_entry_hashes.add(entry_hash)
                                new_entries_added = True
            except Exception as e:
                # Log the error but continue processing other files
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                error_entry = f"{timestamp} - Error reading log file {log_file.name}: {str(e)}"
                entry_hash = self.get_hash(error_entry)
                if entry_hash not in self.log_entry_hashes:
                    consolidated_entries.append(error_entry)
                    self.log_entry_hashes.add(entry_hash)
                    new_entries_added = True
        
        # If we added new entries or this is a forced update, update the consolidated file
        if new_entries_added or force:
            # Sort entries by timestamp (first 19 characters)
            consolidated_entries.sort(key=lambda x: x[:19] if len(x) > 19 and x[:19].count('-') == 2 and x[:19].count(':') == 2 else "0000-00-00 00:00:00")
            
            # Write to consolidated log file
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(consolidated_entries))
            
            # Update status
            self.status_label.setText(f"Logs updated at {datetime.datetime.now().strftime('%H:%M:%S')}")
            return True
        return False
    
    def refresh_log(self):
        """Refresh the log display"""
        was_updated = self.consolidate_logs()
        self.is_first_load = False
        
        if self.log_file.exists():
            try:
                # Remember scroll position
                scroll_bar = self.log_content.verticalScrollBar()
                was_at_bottom = scroll_bar.value() == scroll_bar.maximum()
                
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Only update UI if content is actually different to avoid flicker
                if was_updated or self.log_content.toPlainText() != content:
                    # Format log content with colored timestamps and without source
                    formatted_content = ""
                    for line in content.splitlines():
                        # Skip empty lines
                        if not line.strip():
                            continue
                            
                        # Check if line contains a timestamp pattern (YYYY-MM-DD HH:MM:SS)
                        if line[:19].count('-') == 2 and line[:19].count(':') == 2:
                            timestamp = line[:19]
                            message = line[20:].strip()  # Skip the hyphen and space after timestamp
                            
                            # Remove source marker if present (completely remove, no conditional check)
                            source_start = message.find('[Source:')
                            if source_start > -1:
                                message = message[:source_start].strip()
                                
                            formatted_content += (
                                f"<span style='color:#3B82F6;'>{timestamp}</span> - "
                                f"<span style='color:#1E293B;'>{message}</span><br>"
                            )
                        else:
                            formatted_content += f"<span style='color:#1E293B;'>{line}</span><br>"
                    
                    self.log_content.setHtml(formatted_content)
                    
                    # Restore scroll to bottom if it was at bottom
                    if was_at_bottom:
                        scroll_bar.setValue(scroll_bar.maximum())
                        
                    self.status_label.setText(f"Logs refreshed at {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                self.log_content.setText(f"Error reading log file: {str(e)}")
                self.status_label.setText("Error Reading Logs")
        else:
            self.log_content.setHtml("<span style='color:#64748B; font-style:italic;'>No logs available yet.</span>")
            self.status_label.setText("No Logs Available")
    
    def toggle_auto_refresh(self, checked):
        """Toggle auto-refresh functionality"""
        if checked:
            self.auto_refresh_btn.setText("Auto Refresh: ON")
            self.update_timer.start()
        else:
            self.auto_refresh_btn.setText("Auto Refresh: OFF")
            self.update_timer.stop()
    
    def clear_logs(self):
        """Clear all logs after confirmation"""
        from ui.utils import create_styled_message_box
        
        confirm = create_styled_message_box(
            self,
            title="Confirm Clear Logs",
            text="Are you sure you want to clear all logs? This cannot be undone.",
            icon=QMessageBox.Icon.Warning,
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            default_button=QMessageBox.StandardButton.No
        )
        
        if confirm.exec() == QMessageBox.StandardButton.Yes:
            try:
                # Clear hash set to prevent reloading old entries
                self.log_entry_hashes.clear()
                self.last_file_modified_times.clear()
                
                # Clear all individual log files - use glob.glob to ensure we get all files
                import glob
                log_files = glob.glob(str(self.log_dir / "*.txt"))
                for log_file_path in log_files:
                    log_file = Path(log_file_path)
                    try:
                        # Empty the file contents while preserving the file
                        with open(log_file, 'w', encoding='utf-8') as f:
                            f.write("")
                    except Exception as e:
                        print(f"Error clearing log file {log_file}: {str(e)}")
                
                # Write a fresh start message to consolidated log
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"{timestamp} - Logs cleared by user\n")
                
                # Add the new message to the hash set
                entry_hash = self.get_hash(f"{timestamp} - Logs cleared by user")
                self.log_entry_hashes.add(entry_hash)
                
                # Ensure we update the status immediately
                self.refresh_log()
                self.status_label.setText("All logs cleared successfully")
            except Exception as e:
                error_box = create_styled_message_box(
                    self,
                    title="Error",
                    text=f"Failed to clear logs: {str(e)}",
                    icon=QMessageBox.Icon.Critical
                )
                error_box.exec()
    
    def closeEvent(self, event):
        """Stop timer when widget is closed"""
        self.update_timer.stop()
        super().closeEvent(event)