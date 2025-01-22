import sys
import traceback
import datetime
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton
from app.core.services.CrawlerThread import CrawlerThread
from app.core.services.AblyThread import AblyThread
from app.core.utils.FileMaker import FileMaker, Logger
from app.ui.styles import window_appearance as win_appear
from app.ui.styles import button_style as bt_styles
from app.ui.widgets import windows as win
from app.ui.widgets import buttons as btn
from app.ui.widgets.target_site_select import TargetSelectBtn, TargetSiteSelect

logger = Logger(name="main_window", log_file="main_window.log").get_logger()

START_TIME = datetime.datetime(2024, 12, 27, 9, 00)  # 샘플 사용 시작 시간
LIMIT_TIME = datetime.timedelta(minutes=60 * 24 * 14)  # 사용 가능한 제한 시간 설정
MAX_TITLES = 5  # 한 번에 수집할 블로그 타이틀의 최대 개수 설정


class MainWindow(QtWidgets.QMainWindow):
    _signalMusinsaSelectBtn = Signal(bool)
    _signalAblySelectBtn = Signal(bool)

    def __init__(self):
        super().__init__()

        self.crawler_thread = None  # 크롤러 스레드 인스턴스를 저장할 변수 초기화

        self.animation_index = 0  # 애니메이션 상태를 저장할 변수

        self._scraping_completed_count = 0

        self._max_scraping_size = 0

        self.animation_timer = QtCore.QTimer()  # 애니메이션에 사용할 QTimer 생성

        self.start_time = START_TIME
        self.sample_time_limit = LIMIT_TIME

        # 타이머에 애니메이션 처리 함수 연결
        self.animation_timer.timeout.connect(self.animate_buttons)

        self._stateMusinsaSelectBtn = False
        self._stateAblySelectBtn = False

        self.mountWidgets()  # UI 초기화 함수 호출

    def mountWidgets(self):
        self.setWindowTitle("크롤러 v.1.4.0")  # 창 제목 설정

        central_widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(central_widget)

        self._mountWgCentral(layout=layout, wg=central_widget)

        self._mountWgAppearance()

        self._mountWgWindowControls(layout)

        self._mountWgHeaderWindow(layout)

        self._mountScrapingCountWindow(layout)

        self._mountWgTargetSites(layout)

        self._mountWgScrapingSizeBox(layout)

        self._mountWgBtns(layout)

        self._mountWindowSize(scale=0.75)

        ## 배경색과 코너 radius는 이 클래스에서 정의한 paintEvent, resizeEvent 참조

        # self.setLayout(layout)  # 설정된 레이아웃 적용

        self.setCentralWidget(central_widget)

    def start_crawling(self):
        if not self.check_time_limit():
            return

        if self._stateMusinsaSelectBtn == True and self._stateAblySelectBtn == True:
            print("크롤링 사이트를 하나만 선택하세요")
            QtWidgets.QMessageBox.warning(
                self, "경고", "사이트를 하나만 선택하세요."  # 타이틀
            )
            return

        elif self._stateMusinsaSelectBtn == False and self._stateAblySelectBtn == False:
            print("크롤링 사이트를 선택하지 않았어요")
            QtWidgets.QMessageBox.warning(
                self, "경고", "사이트가 선택되지 않았어요."  # 타이틀
            )
            return
        
        self._scraping_completed_count = 0

        self.save_button.setStyleSheet("background-color: lightcoral; color: white;")
        self.save_button.setEnabled(False)
        self.animation_index = 0
        self.animation_timer.start(500)
        self.start_button.setText("크롤링 중 (브랜드 0개 수집완료)")  # 초기 상태 설정
        self.start_button.setEnabled(False)

        self._update_wg_header_window(f"크롤링 시작!")

        # 사용자가 입력한 max_scraping_size 값을 가져옴
        self._max_scraping_size = self._scraping_size_input.value()

        # 크롤러 스레드 생성 및 설정
        url = "https://www.musinsa.com/app/brand_event/lists"

        if self._stateMusinsaSelectBtn == True and self._stateAblySelectBtn == False:
            print("무신사 크롤링 시작합니다.")
            self.crawler_thread = CrawlerThread(url)
            self.crawler_thread.max_scraping_size = self._max_scraping_size

            self.crawler_thread.start()

        elif self._stateMusinsaSelectBtn == False and self._stateAblySelectBtn == True:
            print("에이블리 크롤링 시작합니다.")
            self.crawler_thread = AblyThread()
            self.crawler_thread.max_scraping_size = self._max_scraping_size
            self.crawler_thread.start()

        elif self._stateMusinsaSelectBtn == True and self._stateAblySelectBtn == True:
            print("크롤링 사이트를 하나만 선택하세요")
            QtWidgets.QMessageBox.warning(
                self, "경고", "사이트를 하나만 선택하세요."  # 타이틀
            )
            return

        else:
            print("크롤링 사이트를 선택하지 않았어요")
            QtWidgets.QMessageBox.warning(
                self, "경고", "사이트가 선택되지 않았어요."  # 타이틀
            )
            return

        self._connect_signals()

    def _mountWgCentral(self, layout: QVBoxLayout, wg: QtWidgets.QWidget):
        # 부모 레이아웃 마진과 간격 제거
        layout.setContentsMargins(8, 0, 8, 0)  # 좌, 상, 우, 하 (좌우 20px, 상하 0px)

        # 레이아웃 정렬 옵션 설정 (수직 가운데 정렬)
        layout.setAlignment(QtCore.Qt.AlignVCenter)

        layout.setSpacing(10)  # 위젯 간 간격 제거

        wg.setStyleSheet(
            """
        * {
            margin: 0;
            padding: 0;
            font-size: 14px;  /* 글씨 크기 설정 */
        }
        """
        )

    def _mountWgBtns(self, layout: QVBoxLayout):

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

    def _mountWindowSize(self, scale, width=430, height=932):
        scaled = (int(width * scale), int(height * scale))
        self.setFixedSize(*scaled)

    def _mountWgAppearance(self):
        win_appear.set_translucent_background(self)
        win_appear.apply_drop_shadow(self)

    def _mountWgWindowControls(self, layout: QVBoxLayout):
        self.window_controls = btn.WindowControls(self)
        self.window_controls.add_to_main_layout(layout)

    def _mountWgHeaderWindow(self, layout: QVBoxLayout):
        # 상태 로그
        self._wg_header_window = win.StatusDisplayer(
            "크롤러가 임무를 기다리고 있어요", fixed_height=60, color="#ffffff"
        )
        self._wg_header_window.setStyleSheet(
            """
                QTextEdit {
                    margin: 0;  /* 모든 마진 제거 */
                    padding: 0;  /* 필요하다면 패딩도 제거 */
                    border: red;  /* 테두리 제거 */
                }
            """
        )
        layout.addWidget(self._wg_header_window)

    def _update_wg_header_window(self, message):
        if isinstance(message, int):
            message = str(message)
        self._wg_header_window.setPlainText(message)

    def _mountScrapingCountWindow(self, layout: QVBoxLayout):
        self._wg_scraping_count_window = win.StatusDisplayer(
            f"현재 수집된 브랜드 {self._scraping_completed_count}/{self._max_scraping_size}개",
            fixed_height=400,
            color="#ffffff",
        )

        self._wg_scraping_count_window.setContentsMargins(0, 0, 0, 0)

        self._wg_scraping_count_window.setStyleSheet(
            """
                QTextEdit {
                    margin: 0;  /* 모든 마진 제거 */
                    padding: 0;  /* 필요하다면 패딩도 제거 */
                    border: none;  /* 테두리 제거 */

                }
            """
        )

        layout.addWidget(self._wg_scraping_count_window)

    def _update_ui_scraping_count_window(self, message):
        if isinstance(message, int):
            message = str(message)
        self._wg_scraping_count_window.setPlainText(message)

    def _mountWgScrapingSizeBox(self, layout: QVBoxLayout):
        # 수평 레이아웃 생성
        horizontal_layout = QtWidgets.QHBoxLayout()

        # 라벨 생성 및 추가
        scraping_label = QtWidgets.QLabel("크롤링 개수:")
        horizontal_layout.addWidget(scraping_label)  # 수평 레이아웃에 라벨 추가

        # QSpinBox 생성 및 추가
        self._scraping_size_input = QtWidgets.QSpinBox()
        self._scraping_size_input.setRange(1, 500)
        self._scraping_size_input.setValue(50)
        self._scraping_size_input.setSingleStep(10)
        self._scraping_size_input.setSuffix(" 개")

        # 크기 정책 및 최소 너비 설정
        self._scraping_size_input.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,  # 가로로 확장 가능
            QtWidgets.QSizePolicy.Fixed,  # 세로는 고정
        )
        self._scraping_size_input.setMinimumWidth(200)  # 최소 너비 설정

        horizontal_layout.addWidget(
            self._scraping_size_input
        )  # 수평 레이아웃에 SpinBox 추가

        # 라벨과 SpinBox 간격 설정
        horizontal_layout.setSpacing(5)  # 간격을 5픽셀로 설정 (원하는 대로 조정 가능)

        # 수평 레이아웃을 메인 레이아웃에 추가
        layout.addLayout(horizontal_layout)

    def _mountWgTargetSites(self, layout: QVBoxLayout):
        wg_target_sites = TargetSiteSelect(parent=self)

        self._wgMusinsaSelectBtn = TargetSelectBtn(
            signal=self._signalMusinsaSelectBtn,
            text="무신사",
            setState=self._setStateMusinsaSelectBtn,
        )

        self._wgAbltSelectBtn = TargetSelectBtn(
            signal=self._signalAblySelectBtn,
            text="에이블리",
            setState=self._setStateAblySelectBtn,
        )

        wg_target_sites.addWidget(self._wgMusinsaSelectBtn)
        wg_target_sites.addWidget(self._wgAbltSelectBtn)

        layout.addLayout(wg_target_sites)

    def _setStateMusinsaSelectBtn(self):
        if self._stateMusinsaSelectBtn == False:
            self._stateMusinsaSelectBtn = True

            self._wgMusinsaSelectBtn.setStyleSheet(
                bt_styles.get_style_target_site_btn(active=self._stateMusinsaSelectBtn)
            )

        else:
            self._stateMusinsaSelectBtn = False
            self._wgMusinsaSelectBtn.setStyleSheet(
                bt_styles.get_style_target_site_btn(active=self._stateMusinsaSelectBtn)
            )

        self._signalMusinsaSelectBtn.emit(self._stateMusinsaSelectBtn)

    def _setStateAblySelectBtn(self):
        if self._stateAblySelectBtn == False:
            self._stateAblySelectBtn = True
            self._wgAbltSelectBtn.setStyleSheet(
                bt_styles.get_style_target_site_btn(active=self._stateAblySelectBtn)
            )
        else:
            self._stateAblySelectBtn = False
            self._wgAbltSelectBtn.setStyleSheet(
                bt_styles.get_style_target_site_btn(active=self._stateAblySelectBtn)
            )
        self._signalAblySelectBtn.emit(self._stateAblySelectBtn)

    def check_time_limit(self):
        current_time = datetime.datetime.now()
        # if current_time - self.start_time > self.sample_time_limit:
        #     QtWidgets.QMessageBox.warning(
        #         self, "사용 시간 종료", "샘플 사용 시간이 끝났어요."
        #     )
        #     self.start_button.setEnabled(False)  # 크롤링 시작 버튼 비활성화
        #     return False
        return True

    def _connect_signals(self):
        self.crawler_thread.update_progress.connect(self._set_scraping_count)

        self.crawler_thread.update_progress.connect(
            lambda count: self._update_ui_scraping_count_window(
                f"현재 수집된 브랜드 {self._scraping_completed_count}/{self._max_scraping_size}개"
            )
        )

        self.crawler_thread.error_occurred.connect(logger.exception)

        self.crawler_thread.finished.connect(self.enable_save_button)

    def _set_scraping_count(self, count):
        """실시간으로 수집된 브랜드 수 상태를 로그에 반영."""
        self._scraping_completed_count = count  # 현재 수집된 브랜드 수 업데이트

    def animate_buttons(self):
        dots = "." * (self.animation_index % 4)
        self.save_button.setText(f"엑셀 저장 준비 중{dots}")
        self.start_button.setText(
            f"크롤링 중 {self._scraping_completed_count}/{self._max_scraping_size} 개 수집{dots}"
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
                self._update_wg_header_window(f"결과물이 {file_path}에 저장되었습니다.")
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.exception("엑셀 저장 중 오류 발생", error_trace)

    def _refresh_message(self, message):
        if isinstance(message, int):
            message = str(message)
        self._wg_header_window.setPlainText(message)

    def paintEvent(self, event):
        """둥근 모서리 배경 그리기"""
        win_appear.paint_rounded_background(self, event, radius=30)

    def resizeEvent(self, event):
        """리사이즈 시 둥근 모서리 재적용"""
        win_appear.apply_rounded_corners(self, radius=30)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = True
            self.drag_start_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_start_position)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = False
