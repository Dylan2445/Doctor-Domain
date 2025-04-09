from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from ..components.tool_card import ToolCard

class EmailToolsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QLabel("Email Management Tools")
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 600;
            color: #1E293B;
            padding-bottom: 5px;
        """)
        layout.addWidget(header)

        # Cards
        cards_widget = QWidget()
        cards_layout = QVBoxLayout(cards_widget)
        cards_layout.setSpacing(15)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        # Function cards container
        functions_widget = QWidget()
        functions_layout = QHBoxLayout(functions_widget)
        functions_layout.setSpacing(15)
        functions_layout.setContentsMargins(0, 0, 0, 0)

        sanitizer_card = ToolCard(
            "Email Sanitizer 🧼",
            "Finds and updates any user email addresses that are not intended domains.",
            "sanitize.png",
            "scripts/email_sanitizer.py"
        )
        injector_card = ToolCard(
            "Email Injector 💉",
            "Updates all accounts missing an email address by assigning a placeholder domain.",
            "inject.png",
            "scripts/email_injector.py"
        )

        functions_layout.addWidget(sanitizer_card)
        functions_layout.addWidget(injector_card)
        cards_layout.addWidget(functions_widget)

        # Coming soon card
        coming_soon_card = ToolCard(
            "Additional Tools Coming Soon ⏳",
            "New Features Coming Soon!",
            "soon.png",
            None
        )
        cards_layout.addWidget(coming_soon_card)

        layout.addWidget(cards_widget)
        layout.addStretch()