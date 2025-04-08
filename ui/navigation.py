from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from pathlib import Path

class NavigationButton(QPushButton):
    def __init__(self, text, icon_path=None):
        super().__init__()
        self.setText(text)
        if icon_path:
            self.setIcon(QIcon(str(Path(__file__).parent / "icons" / icon_path)))
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                border: none;
                text-align: left;
                padding: 12px 15px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 8px;
                margin: 2px 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            QPushButton[Active=true] {
                background: #3B82F6;
                color: white;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)