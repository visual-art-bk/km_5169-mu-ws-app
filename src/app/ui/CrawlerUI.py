import sys
import traceback
import datetime
from PyQt5 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from app.core.services.CrawlerThread import CrawlerThread

START_TIME = datetime.datetime(2024, 11, 20, 13, 30)  # 샘플 사용 시작 시간
LIMIT_TIME = datetime.timedelta(minutes=720)  # 사용 가능한 제한 시간 설정
MAX_TITLES = 5  # 한 번에 수집할 블로그 타이틀의 최대 개수 설정

# 사용자 인터페이스 정의를 위한 QWidget 상속 클래스
class CrawlerUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()  # UI 초기화 함수 호출

        self.crawler_thread = None  # 크롤러 스레드 인스턴스를 저장할 변수 초기화

        self.animation_index = 0  # 애니메이션 상태를 저장할 변수

        self.animation_timer = QtCore.QTimer()  # 애니메이션에 사용할 QTimer 생성

        # 샘플 사용 시간 관련 상수 초기화
        self.start_time = START_TIME

        self.sample_time_limit = LIMIT_TIME


        # 타이머에 애니메이션 처리 함수 연결
        self.animation_timer.timeout.connect(self.animate_buttons)

        
        # 창을 최상단에 고정
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)

    def initUI(self):
        
        # UI 초기화 및 위젯 구성
        self.setWindowTitle("Tistory Blog Crawler")  # 창 제목 설정
        
        layout = QtWidgets.QVBoxLayout()  # 레이아웃 설정



        # URL 입력 필드 및 라벨 추가
        self.url_label = QtWidgets.QLabel("크롤링할 티스토리 블로그 URL 입력:")
        
        layout.addWidget(self.url_label)
        
        self.url_input = QtWidgets.QLineEdit(self)
        
        layout.addWidget(self.url_input)


        # 상태 메시지 및 결과 출력 필드
        self.status_label = QtWidgets.QTextEdit("현재 상태: 대기 중 11/20:13:15")
        
        self.status_label.setReadOnly(True)  # 읽기 전용으로 설정
        

        layout.addWidget(self.status_label)

        # 크롤링 시작 버튼 생성
        self.start_button = QtWidgets.QPushButton("크롤링 시작")
        
        self.start_button.clicked.connect(
            self.start_crawling
        )  # 클릭 시 실행될 함수 연결

        layout.addWidget(self.start_button)



        # 결과 저장 버튼 생성
        self.save_button = QtWidgets.QPushButton("메모장으로 결과물 저장")
        
        self.save_button.setEnabled(False)  # 초기에는 비활성화
        
        self.save_button.clicked.connect(
            self.save_results_to_file
        )  # 클릭 시 파일 저장 함수 연결
        

        layout.addWidget(self.save_button)

        # 결과 출력 필드 생성
        self.result_text = QtWidgets.QTextEdit()
        
        self.result_text.setReadOnly(True)  # 읽기 전용으로 설정
        
        layout.addWidget(self.result_text)

        self.setLayout(layout)  # 설정된 레이아웃 적용

    def log_status(self, message):
        # 상태 메시지를 기록하는 메서드
        self.status_label.append(message)

    def check_time_limit(self):
        # 샘플 사용 시간이 만료되었는지 확인하는 메서드
        current_time = datetime.datetime.now()

        if current_time - self.start_time > self.sample_time_limit:
            QtWidgets.QMessageBox.warning(
                self, "사용 시간 종료", "샘플 사용 시간이 끝났어요."
            )
            self.start_button.setEnabled(False)  # 크롤링 시작 버튼 비활성화

            return False

        return True

    def start_crawling(self):
        # 크롤링 시작 버튼 클릭 시 호출되는 메서드
        if not self.check_time_limit():  # 시간 제한 확인
            return

        # UI 업데이트: 저장 버튼 비활성화 및 애니메이션 시작
        self.save_button.setStyleSheet("background-color: lightcoral; color: white;")
        self.save_button.setEnabled(False)
        self.animation_index = 0
        self.animation_timer.start(500)  # 500ms 간격으로 애니메이션 실행
        self.start_button.setText("크롤링 중")
        self.start_button.setEnabled(False)

        # 입력된 URL 가져오기
        url = self.url_input.text()
        if not url:  # URL이 비어 있으면 오류 메시지 표시
            self.display_error("URL이 입력되지 않았습니다.")
            return
        self.log_status(f"크롤링 시작합니다 - {url}")

        # 크롤링 스레드 시작
        self.crawler_thread = CrawlerThread(url)  # URL을 매개변수로 전달

        self.crawler_thread.update_status.connect(self.log_status)  # 상태 업데이트 연결

        self.crawler_thread.update_result.connect(
            self.result_text.append
        )  # 결과 업데이트 연결

        self.crawler_thread.error_occurred.connect(self.display_error)  # 오류 처리 연결

        self.crawler_thread.finished.connect(
            self.enable_save_button
        )  # 크롤링 완료 처리 연결

        self.crawler_thread.start()  # 스레드 시작

    def animate_buttons(self):
        # 애니메이션 효과 적용 메서드
        dots = "." * (self.animation_index % 4)  # 점(.)을 증가시키며 표시
        self.save_button.setText(f"메모장 저장 준비 중{dots}")
        self.start_button.setText(f"크롤링 중{dots}")
        self.animation_index += 1

    def enable_save_button(self):
        # 크롤링 완료 후 UI 업데이트 메서드
        self.animation_timer.stop()  # 애니메이션 중지
        self.save_button.setEnabled(True)
        self.save_button.setStyleSheet("background-color: lightgreen; color: black;")
        self.save_button.setText("메모장으로 결과물 저장")
        self.start_button.setText("크롤링 시작")
        self.start_button.setEnabled(True)

    def save_results_to_file(self):
        # 크롤링 결과를 파일로 저장하는 메서드
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "메모장으로 결과물 저장",
            "",
            "Text Files (*.txt);;All Files (*)",
            options=options,
        )

        if file_path:  # 저장 경로가 선택된 경우
            with open(file_path, "w", encoding="utf-8") as f:
                for title in self.crawler_thread.results:
                    f.write(f"{title}\n")
            self.log_status(f"결과물이 {file_path}에 저장되었습니다.")

    def display_error(self, message, error_trace=""):
        # 오류 메시지를 UI에 표시하는 메서드
        self.log_status("오류 발생!")  # 상태창에 메시지 추가

        self.result_text.append("\n오류 메시지:")  # 오류 결과창에 추가

        self.result_text.setTextColor(QtGui.QColor("red"))  # 오류 메시지 색상 변경


        error_message = f"{message}\n\n세부 정보:\n{error_trace}"  # 상세 메시지 구성
        self.result_text.append(error_message)  # 상세 메시지 추가

        self.result_text.setTextColor(QtGui.QColor("black"))  # 색상 초기화
