from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QHBoxLayout, QPushButton, QFrame, QLabel,
                            QGraphicsDropShadowEffect, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QColor
from pathlib import Path
import datetime
import hashlib

class LogOverlay(QWidget):
    """Modern overlay widget to display logs in real-time"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_dir = Path(__file__).parent.parent.parent / "scripts" / "Logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Consolidated log file
        self.log_file = self.log_dir / "consolidated_log.txt"
        
        # Store hashes of log entries to avoid duplicates
        self.log_entry_hashes = set()
        self.last_file_modified_times = {}
        
        # Create timer for auto-refresh
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_log)
        self.update_timer.setInterval(3000)  # Refresh every 3 seconds
        
        # Set attributes for the overlay
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animation control
        self.collapsed_height = 40
        self.expanded_height = 300
        self.is_expanded = False
        self.expand_animation = None
        
        self.setup_ui()
        self.refresh_log()
        self.update_timer.start()
    
    def setup_ui(self):
        # Set overlay style - using a frame for better shadow effects
        self.main_frame = QFrame(self)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(-5)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.main_frame.setGraphicsEffect(shadow)
        
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.98);
                border: 1px solid #E2E8F0;
                border-radius: 14px 14px 0 0;
            }
        """)
        
        # Set frame to fill the overlay widget
        frame_layout = QVBoxLayout(self)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(self.main_frame)
        
        # Main layout inside the frame
        main_layout = QVBoxLayout(self.main_frame)
        main_layout.setContentsMargins(20, 10, 20, 16)
        main_layout.setSpacing(10)
        
        # Drag handle at the top
        self.handle_bar = QWidget()
        handle_layout = QHBoxLayout(self.handle_bar)
        handle_layout.setContentsMargins(0, 0, 0, 5)
        handle_layout.setSpacing(10)
        
        # Drag indicator
        drag_indicator = QFrame()
        drag_indicator.setFixedSize(50, 5)
        drag_indicator.setStyleSheet("""
            background-color: #CBD5E1;
            border-radius: 2.5px;
        """)
        
        # Add to handle layout
        handle_layout.addStretch(1)
        handle_layout.addWidget(drag_indicator, alignment=Qt.AlignmentFlag.AlignCenter)
        handle_layout.addStretch(1)
        
        main_layout.addWidget(self.handle_bar)
        
        # Title row
        title_row = QWidget()
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("📋 Logs")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1E293B;
        """)
        
        # Auto refresh indicator
        self.status_label = QLabel("Auto-refresh on")
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #059669;
            padding: 2px 8px;
            background: #ECFDF5;
            border-radius: 10px;
        """)
        
        # Control buttons
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(8)
        
        # Auto-refresh toggle
        self.auto_refresh_btn = QPushButton("Auto")
        self.auto_refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setChecked(True)
        self.auto_refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #EFF6FF;
                color: #3B82F6;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:checked {
                background-color: #3B82F6;
                color: white;
            }
            QPushButton:hover:checked {
                background-color: #2563EB;
            }
            QPushButton:hover:!checked {
                background-color: #DBEAFE;
            }
        """)
        self.auto_refresh_btn.toggled.connect(self.toggle_auto_refresh)
        
        # Full logs button
        self.view_full_logs_btn = QPushButton("Full Logs")
        self.view_full_logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_full_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #3B82F6;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #EFF6FF;
            }
        """)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #64748B;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 4px;
                max-width: 22px;
                max-height: 22px;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                color: #DC2626;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.hide)
        
        # Add to control layout
        control_layout.addWidget(self.auto_refresh_btn)
        control_layout.addWidget(self.view_full_logs_btn)
        control_layout.addWidget(close_btn)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.status_label)
        title_layout.addStretch()
        title_layout.addWidget(control_widget)
        
        # Container for the content that will be shown/hidden
        self.content_container = QWidget()
        content_container_layout = QVBoxLayout(self.content_container)
        content_container_layout.setContentsMargins(0, 0, 0, 0)
        content_container_layout.setSpacing(10)
        
        # Add title row to the content container
        content_container_layout.addWidget(title_row)
        
        # Log content with improved styling
        self.log_content = QTextEdit()
        self.log_content.setReadOnly(True)
        self.log_content.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E2E8F0;
                background-color: #F8FAFC;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                color: #1E293B;
                padding: 12px;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                border: none;
                background: #F1F5F9;
                width: 10px;
                border-radius: 5px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Bottom row with refresh button
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Refresh button
        self.manual_refresh_btn = QPushButton("Refresh")
        self.manual_refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manual_refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #3B82F6;
                border: 1px solid #DBEAFE;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #3B82F6;
            }
        """)
        self.manual_refresh_btn.clicked.connect(self.refresh_log)
        
        bottom_layout.addWidget(self.manual_refresh_btn)
        bottom_layout.addStretch()
        
        # Add components to the content container
        content_container_layout.addWidget(self.log_content)
        content_container_layout.addWidget(bottom_row)
        
        # Add the content container to the main layout
        main_layout.addWidget(self.content_container)
        
        # Set initial state - collapsed to show just the handle
        self.content_container.hide()
    
    def get_hash(self, text):
        """Create a hash for the log entry to detect duplicates"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def refresh_log(self):
        """Refresh the log display with the most recent entries"""
        if self.log_file.exists():
            try:
                # Remember scroll position
                scroll_bar = self.log_content.verticalScrollBar()
                was_at_bottom = scroll_bar.value() == scroll_bar.maximum()
                
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Format log content with colored timestamps
                formatted_content = ""
                lines = content.splitlines()
                # Show only the most recent 50 lines for the overlay
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                
                for line in recent_lines:
                    # Skip empty lines
                    if not line.strip():
                        continue
                        
                    # Check if line contains a timestamp pattern (YYYY-MM-DD HH:MM:SS)
                    if line[:19].count('-') == 2 and line[:19].count(':') == 2:
                        timestamp = line[:19]
                        message = line[20:].strip()  # Skip the hyphen and space after timestamp
                        
                        # Remove source marker if present
                        source_start = message.find('[Source:')
                        if source_start > -1:
                            message = message[:source_start].strip()
                            
                        formatted_content += (
                            f"<div style='margin-bottom:4px;'>"
                            f"<span style='color:#3B82F6; font-weight:500;'>{timestamp}</span> - "
                            f"<span style='color:#1E293B;'>{message}</span>"
                            f"</div>"
                        )
                    else:
                        formatted_content += f"<div style='margin-bottom:4px; color:#1E293B;'>{line}</div>"
                
                self.log_content.setHtml(formatted_content)
                
                # Always scroll to the bottom to show most recent logs
                scroll_bar.setValue(scroll_bar.maximum())
            except Exception as e:
                self.log_content.setText(f"Error reading log file: {str(e)}")
        else:
            self.log_content.setHtml("<span style='color:#64748B; font-style:italic;'>No logs available yet.</span>")
    
    def toggle_auto_refresh(self, checked):
        """Toggle auto-refresh functionality"""
        if checked:
            self.status_label.setText("Auto-refresh on")
            self.status_label.setStyleSheet("""
                font-size: 12px;
                color: #059669;
                padding: 2px 8px;
                background: #ECFDF5;
                border-radius: 10px;
            """)
            self.update_timer.start()
        else:
            self.status_label.setText("Auto-refresh off")
            self.status_label.setStyleSheet("""
                font-size: 12px;
                color: #DC2626;
                padding: 2px 8px;
                background: #FEF2F2;
                border-radius: 10px;
            """)
            self.update_timer.stop()
    
    def connect_full_logs_button(self, callback):
        """Connect the View Full Logs button to a callback"""
        self.view_full_logs_btn.clicked.connect(callback)
    
    def toggle_expansion(self, animate=True):
        """Toggle between expanded and collapsed states with smooth animation"""
        self.is_expanded = not self.is_expanded
        
        # Stop any running animation
        if self.expand_animation and self.expand_animation.state() == QPropertyAnimation.State.Running:
            self.expand_animation.stop()
        
        if animate:
            # Create animation for smooth expansion/collapse
            self.expand_animation = QPropertyAnimation(self, b"geometry")
            self.expand_animation.setDuration(250)  # Animation duration in milliseconds
            self.expand_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            current_geometry = self.geometry()
            parent_width = self.parentWidget().width() if self.parentWidget() else self.width()
            
            if self.is_expanded:
                # Expand animation
                self.content_container.show()
                target_geometry = QRect(
                    20,  # Left margin
                    self.parentWidget().height() - self.expanded_height,
                    parent_width - 40,  # Full width minus margins
                    self.expanded_height
                )
                self.expand_animation.setStartValue(current_geometry)
                self.expand_animation.setEndValue(target_geometry)
                self.refresh_log()  # Refresh logs when expanding
            else:
                # Collapse animation
                target_geometry = QRect(
                    20,  # Left margin
                    self.parentWidget().height() - self.collapsed_height,
                    parent_width - 40,  # Full width minus margins
                    self.collapsed_height
                )
                self.expand_animation.setStartValue(current_geometry)
                self.expand_animation.setEndValue(target_geometry)
                self.expand_animation.finished.connect(lambda: self.content_container.hide())
            
            self.expand_animation.start()
        else:
            # No animation, just change state immediately
            if self.is_expanded:
                self.content_container.show()
                self.setGeometry(
                    20,
                    self.parentWidget().height() - self.expanded_height,
                    self.parentWidget().width() - 40,
                    self.expanded_height
                )
                self.refresh_log()
            else:
                self.content_container.hide()
                self.setGeometry(
                    20,
                    self.parentWidget().height() - self.collapsed_height,
                    self.parentWidget().width() - 40,
                    self.collapsed_height
                )
    
    def show(self):
        """Override show method to ensure proper initialization"""
        super().show()
        # Start in collapsed state
        self.is_expanded = False
        self.content_container.hide()
    
    def closeEvent(self, event):
        """Stop timer when widget is closed"""
        self.update_timer.stop()
        super().closeEvent(event)
    
    def mousePressEvent(self, event):
        """Handle click on the overlay to expand/collapse"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.handle_bar.geometry().contains(event.position().toPoint()):
                self.toggle_expansion()
        super().mousePressEvent(event)