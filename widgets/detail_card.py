"""
detail_card.py
==============

Reusable widget for displaying one weather detail.

Each card displays:
    - Animated Lottie icon
    - Title
    - Value
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QFrame

from PyQt5.QtSvg import QSvgWidget
from managers.icon_manager import IconManager

class DetailCard(QFrame):
    """
    Reusable weather detail card.
    """

    def __init__(self):
        super().__init__()

        self.setObjectName("detailCard")

        self.create_widgets()
        self.create_layout()
        self.apply_styles()

    def create_widgets(self):
        self.icon_widget = QSvgWidget()
        self.icon_widget.setFixedSize(64, 64)

        self.title_label = QLabel()
        self.value_label = QLabel()


        self.title_label.setAlignment(Qt.AlignCenter)
        self.value_label.setAlignment(Qt.AlignCenter)

        self.title_label.setObjectName("detailTitle")
        self.value_label.setObjectName("detailValue")

    def create_layout(self):
        layout = QVBoxLayout()

        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(
            self.icon_widget,
            alignment=Qt.AlignCenter
        )

        layout.addWidget(
            self.title_label,
            alignment=Qt.AlignCenter
        )

        layout.addWidget(
            self.value_label,
            alignment=Qt.AlignCenter
        )

        self.setLayout(layout)

    def apply_styles(self):

        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Raised)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(130, 140)

    def set_title(self, title: str):
        self.title_label.setText(title)

    def set_value(self, value: str):
        self.value_label.setText(value)


    def set_icon(self, detail_name: str):
        """
        Display the requested SVG icon.
        """

        icon_path = IconManager.get_detail_icon(detail_name)

        self.icon_widget.load(icon_path)



