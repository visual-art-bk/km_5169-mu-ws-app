from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget


class WindowControls:
    """창의 최소화, 최대화 및 닫기 버튼을 추가하는 클래스"""

    def __init__(self, parent: QWidget):
        self.parent = parent
        self.is_maximized = False
        self.controls_layout = QHBoxLayout()

        self.minimize_button = self.create_button("🗕", self.parent.showMinimized)
        self.maximize_button = self.create_button("🗖", self.toggle_maximize_restore)
        self.close_button = self.create_button("✕", self.parent.close)

        self._add_buttons_to_layout()

    def create_button(self, text, callback):
        """버튼을 생성하고 콜백을 연결합니다."""
        button = QPushButton(text)
        button.setFixedSize(30, 30)
        button.clicked.connect(callback)
        return button

    def toggle_maximize_restore(self):
        """최대화 또는 복원 상태 전환"""
        if self.is_maximized:
            self.parent.showNormal()
        else:
            self.parent.showMaximized()
        self.is_maximized = not self.is_maximized

    def _add_buttons_to_layout(self):
        """버튼 레이아웃에 버튼을 추가합니다."""
        self.controls_layout.addWidget(self.minimize_button)
        self.controls_layout.addWidget(self.maximize_button)
        self.controls_layout.addWidget(self.close_button)

    def add_to_main_layout(self, main_layout: QVBoxLayout):
        """컨트롤 레이아웃을 메인 레이아웃에 추가합니다."""
        main_layout.addLayout(self.controls_layout)
