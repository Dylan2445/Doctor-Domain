from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from ..components.tool_card import ToolCard

class ComingSoonPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel("Coming Soon")
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
            padding-bottom: 5px;
        """)
        layout.addWidget(header)

        coming_soon_card = ToolCard(
            "More Features Coming Soon 🔜",
            "Stay tuned for additional tools and features that will enhance your email management capabilities.",
            "soon.png",
            None
        )
        
        layout.addWidget(coming_soon_card)
        layout.addStretch()