from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import subprocess
from pathlib import Path

class ToolCard(QFrame):
    def __init__(self, title, description, icon_path, script_path):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # Adjust shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setSpacing(2)  # Reduced from 4
        layout.setContentsMargins(12, 8, 12, 8)  # Reduced vertical margins
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 19px;
            font-weight: 600;
            color: #1E293B;
        """)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            color: #64748B;
            font-size: 13px;
            line-height: 130%;
            margin-bottom: 2px;
        """)
        desc_label.setWordWrap(True)
        
        run_btn = QPushButton("Coming Soon" if script_path is None else "Run Tool")
        run_btn.setEnabled(script_path is not None)
        run_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 5px;
                font-weight: 500;
                font-size: 13px;
                margin-top: 2px;
            }
            QPushButton:disabled {
                background: #94A3B8;
            }
            QPushButton:hover:!disabled {
                background: #2563EB;
            }
        """)
        run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if script_path:
            run_btn.clicked.connect(lambda: self.run_script(script_path))
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(run_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def run_script(self, script_path):
        try:
            subprocess.run(["powershell", "-File", script_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running script: {e}")