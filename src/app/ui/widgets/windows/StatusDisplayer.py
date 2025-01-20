from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QTextCursor

class StatusDisplayer(QTextEdit):
    def __init__(self, initial_text="", max_lines=10, fixed_height=100, color="#f0f0f0"):
        super().__init__(initial_text)
        self.setReadOnly(True)
        self.set_background_color(color)  # 배경색 설정
        self.setFixedHeight(fixed_height)  # 고정 높이 설정
        self.max_lines = max_lines  # 최대 줄 수 제한

    def set_background_color(self, color: str):
        """배경색을 설정"""
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {color};
                border: none;  /* 기본 테두리 제거 */
            }}
        """)

    def append_text(self, text: str):
        """텍스트를 추가하고, 최대 줄 수를 넘으면 오래된 텍스트를 제거"""
        # 텍스트 추가
        self.append(text)

        # 현재 텍스트의 줄 수 검사
        lines = self.toPlainText().split("\n")
        if len(lines) > self.max_lines:
            # 오래된 텍스트 제거
            lines = lines[-self.max_lines:]
            self.setPlainText("\n".join(lines))
            # 커서를 맨 아래로 이동
            self.moveCursor(QTextCursor.End)
