import sys
import traceback
import datetime
from PySide6 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from app.core.services.CrawlerThread import CrawlerThread
from app.core.utils.FileMaker import FileMaker

START_TIME = datetime.datetime(2024, 12, 10, 9, 00)  # 샘플 사용 시작 시간
LIMIT_TIME = datetime.timedelta(minutes=60 * 24 * 7)  # 사용 가능한 제한 시간 설정
MAX_TITLES = 5  # 한 번에 수집할 블로그 타이틀의 최대 개수 설정


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()  # UI 초기화 함수 호출

        self.crawler_thread = None  # 크롤러 스레드 인스턴스를 저장할 변수 초기화

        self.animation_index = 0  # 애니메이션 상태를 저장할 변수

        self.current_count = 0

        self.animation_timer = QtCore.QTimer()  # 애니메이션에 사용할 QTimer 생성

        self.start_time = START_TIME
        self.sample_time_limit = LIMIT_TIME

        # 타이머에 애니메이션 처리 함수 연결
        self.animation_timer.timeout.connect(self.animate_buttons)

    def initUI(self):
        self.setWindowTitle("크롤러 v.1.3.1")  # 창 제목 설정
        layout = QtWidgets.QVBoxLayout()  # 레이아웃 설정

        self.status_label = QtWidgets.QTextEdit("현재 상태: 대기 중...")
        self.status_label.setReadOnly(True)  # 읽기 전용으로 설정
        layout.addWidget(self.status_label)

        # 최대 크롤링 개수를 설정하는 입력 필드 추가
        self.scraping_size_input = QtWidgets.QSpinBox()
        self.scraping_size_input.setRange(1, 500)  # 1 ~ 500 사이 값 입력 가능
        self.scraping_size_input.setValue(50)  # 기본값 50
        layout.addWidget(QtWidgets.QLabel("최대 크롤링 개수:"))
        layout.addWidget(self.scraping_size_input)

        self.start_button = QtWidgets.QPushButton("크롤링 시작")
        self.start_button.clicked.connect(
            self.start_crawling
        )  # 클릭 시 실행될 함수 연결
        layout.addWidget(self.start_button)

        self.save_button = QtWidgets.QPushButton("엑셀로 결과물 저장")
        self.save_button.setEnabled(False)  # 초기에는 비활성화
        self.save_button.clicked.connect(
            self.save_results_to_file
        )  # 클릭 시 파일 저장 함수 연결
        layout.addWidget(self.save_button)

        self.result_text = QtWidgets.QTextEdit()
        self.result_text.setReadOnly(True)  # 읽기 전용으로 설정
        layout.addWidget(self.result_text)

        self.progress_label = QtWidgets.QLabel("수집된 브랜드 수: 0")  # 초기화

        self.setLayout(layout)  # 설정된 레이아웃 적용

    def log_status(self, message):
        self.status_label.append(message)

    def check_time_limit(self):
        current_time = datetime.datetime.now()
        if current_time - self.start_time > self.sample_time_limit:
            QtWidgets.QMessageBox.warning(
                self, "사용 시간 종료", "샘플 사용 시간이 끝났어요."
            )
            self.start_button.setEnabled(False)  # 크롤링 시작 버튼 비활성화
            return False
        return True

    def start_crawling(self):
        # if not self.check_time_limit():
        #     return

        self.save_button.setStyleSheet("background-color: lightcoral; color: white;")
        self.save_button.setEnabled(False)
        self.animation_index = 0
        self.animation_timer.start(500)
        self.start_button.setText("크롤링 중 (브랜드 0개 수집완료)")  # 초기 상태 설정
        self.start_button.setEnabled(False)

        url = "https://www.musinsa.com/app/brand_event/lists"
        self.log_status(f"크롤링 시작합니다 - {url}")

        # 사용자가 입력한 max_scraping_size 값을 가져옴
        max_scraping_size = self.scraping_size_input.value()

        # 크롤러 스레드 생성 및 설정
        self.crawler_thread = CrawlerThread(url)
        self.crawler_thread.max_scraping_size = max_scraping_size  # 전달

        # Signal 연결
        self.crawler_thread.update_status.connect(self.log_status)
        self.crawler_thread.update_progress.connect(
            self.update_crawling_status
        )  # 수집 상태 업데이트
        self.crawler_thread.error_occurred.connect(self.display_error)
        self.crawler_thread.finished.connect(self.enable_save_button)

        # 스레드 시작
        self.crawler_thread.start()

    def update_crawling_status(self, count):
        """실시간으로 수집된 브랜드 수 상태를 로그에 반영."""
        self.current_count = count  # 현재 수집된 브랜드 수 업데이트

    def animate_buttons(self):
        dots = "." * (self.animation_index % 4)
        self.save_button.setText(f"엑셀 저장 준비 중{dots}")
        self.start_button.setText(
            f"크롤링 중 - 브랜드 {self.current_count}개 수집{dots}"
        )
        self.animation_index += 1

    def enable_save_button(self):
        self.animation_timer.stop()
        self.save_button.setEnabled(True)
        self.save_button.setStyleSheet("background-color: lightgreen; color: black;")
        self.save_button.setText("엑셀로 결과물 저장")
        self.start_button.setText("크롤링 시작")
        self.start_button.setEnabled(True)

    def save_results_to_file(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "엑셀로 결과물 저장",
            "",
            "Excel Files (*.xlsx);;All Files (*)",
            options=options,
        )

        if file_path:
            try:
                FileMaker.save_to_excel_for_musinsa(
                    fixed_columns=[
                        "브랜드 페이지",
                        "브랜드",
                        "상품분류코드(한)",
                        "영문명",
                        "상품분류코드(영)",
                        "상호 / 대표자",
                        "영업소재지",
                        "E-mail",
                        "연락처",
                        "사업자번호",
                        "통신판매업신고",
                    ],
                    file_name=file_path,
                    infos_list=self.crawler_thread.results,
                )
                self.log_status(f"결과물이 {file_path}에 저장되었습니다.")
            except Exception as e:
                error_trace = traceback.format_exc()
                self.display_error("엑셀 저장 중 오류 발생", error_trace)

    def display_error(self, message, error_trace=""):
        self.log_status("오류 발생!")
        self.result_text.append("\n오류 메시지:")
        self.result_text.setTextColor(QtGui.QColor("red"))
        error_message = f"{message}\n\n세부 정보:\n{error_trace}"
        self.result_text.append(error_message)
        self.result_text.setTextColor(QtGui.QColor("black"))
