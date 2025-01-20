from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton


class TargetSiteSelect(QHBoxLayout):
    def __init__(
        self,
        parent,
    ):
        super().__init__()
        self._parent = parent


from typing import Any, Callable, Tuple


class TargetSelectBtn(QPushButton):
    _state_type = Tuple[Any, Callable[[Any], None]]
    _type_set_state = Callable[[Any], None]

    def __init__(
        self,
        signal: Signal,
        setState: _type_set_state,
        text="기본값텍스트",
        width=120,
        height=36,
    ):
        super().__init__()
        self._signal: Signal = signal
        self._width = width
        self._height = height
        self.setText(text)
        self._connectSignal()
        self._connectSetState(setState)

    def _connectSignal(self):
        def onChange(state):
            """"""
            # print(f"자식요소에서의 {state}")  # 로깅용도

        self._signal.connect(lambda changed_state: onChange(changed_state))

    def _connectSetState(self, setState):
        self.clicked.connect(setState)

    def setStyle(self):
        self.setFixedSize(w=self._width, h=self._height)


# btn_styles = """
#         QPushButton {
#             background-color: #FFFFFF;  /* 기본 배경색 흰색 */
#             border-radius: 16px;       /* 테두리를 둥글게 설정 */
#             height: 36px;
#         }
#         QPushButton:pressed {
#             background-color: #E0E0E0; /* 클릭 시 연회색 배경 */
#         }
#         QPushButton:hover {
#             background-color: #F5F5F5; /* 호버 시 밝은 회색 배경 */
#         }
#         """
