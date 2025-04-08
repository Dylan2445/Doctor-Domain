from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from ..components.tool_card import ToolCard

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("Settings")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: 600;
            color: #1E293B;
        """)
        layout.addWidget(header)
        
        config_card = ToolCard(
            "Configure Environment ⚙️",
            "Set up prerequisites and permissions for the email management tools.",
            "config.png",
            "configure_env.ps1"
        )
        
        layout.addWidget(config_card)
        layout.addStretch()