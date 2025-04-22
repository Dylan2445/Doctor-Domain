from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from pathlib import Path

class NavigationButton(QPushButton):
    # New signal for the toggle button
    toggle_clicked = pyqtSignal()
    
    def __init__(self, text, icon_path=None, has_toggle=False):
        super().__init__()
        
        # Create a layout for the button if it has a toggle
        if has_toggle:
            self.container = QWidget()
            layout = QHBoxLayout(self.container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Main button (self) setup
            self.setText(text)
            if icon_path:
                self.setIcon(QIcon(str(Path(__file__).parent / "icons" / icon_path)))
            
            # Toggle button setup
            self.toggle_btn = QPushButton("📋")
            self.toggle_btn.setFixedSize(32, 32)
            self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(70, 120, 220, 0.2);
                    border: none;
                    padding: 5px;
                    border-radius: 4px;
                    margin: 0 5px 0 0;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.15);
                }
                QPushButton[Expanded=true] {
                    background: rgba(59, 130, 246, 0.4);
                }
            """)
            self.toggle_btn.clicked.connect(self.toggle_clicked)
            
            # Add to layout
            layout.addWidget(self, 1)  # 1 means it will take available space
            layout.addWidget(self.toggle_btn)
        else:
            # Standard button setup without toggle
            self.setText(text)
            if icon_path:
                self.setIcon(QIcon(str(Path(__file__).parent / "icons" / icon_path)))
        
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                border: none;
                text-align: left;
                padding: 8px 16px;
                font-size: 15px;
                font-weight: 500;
                border-radius: 6px;
                margin: 2px 12px;
                min-height: 44px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: white;
            }
            QPushButton[Active=true] {
                background: #3B82F6;
                color: white;
            }
            QPushButton[Active=true]:hover {
                background: #2563EB;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def set_toggle_expanded(self, expanded):
        """Set the expanded state of the toggle button"""
        if hasattr(self, 'toggle_btn'):
            self.toggle_btn.setProperty("Expanded", expanded)
            self.toggle_btn.style().unpolish(self.toggle_btn)
            self.toggle_btn.style().polish(self.toggle_btn)
            
            # Update text when expanded state changes
            if expanded:
                self.toggle_btn.setText("✖")
            else:
                self.toggle_btn.setText("📋")
            
    def get_container(self):
        """Return the container widget if this button has a toggle, otherwise return self"""
        return self.container if hasattr(self, 'container') else self