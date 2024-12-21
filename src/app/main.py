import sys
from PySide6 import QtWidgets  # PySide6로 변경 (PyQt5 사용 시 PyQt5로 대체)
from app.ui.main_window import MainWindow  # CrawlerUI 클래스가 정의된 모듈을 가져옵니다.

def main():
    # QApplication 객체 생성 (가장 먼저 실행)
    app = QtWidgets.QApplication(sys.argv)

    # 메인 창 생성
    main_window = MainWindow()
    main_window.show()

    # 이벤트 루프 실행
    sys.exit(app.exec())


if __name__ == "__main__":
    main()  # main 함수 실행
