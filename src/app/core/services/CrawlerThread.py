import sys
import traceback
import datetime
from PyQt5 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

START_TIME = datetime.datetime(2024, 11, 20, 13, 30)  # 샘플 사용 시작 시간
LIMIT_TIME = datetime.timedelta(minutes=720)  # 사용 가능한 제한 시간 설정
MAX_TITLES = 5  # 한 번에 수집할 블로그 타이틀의 최대 개수 설정


class CrawlerThread(QtCore.QThread):
    
    # PyQt Signal 정의: UI 업데이트를 위해 필요한 정보를 전송

    update_status = QtCore.pyqtSignal(str)  # 상태 메시지 업데이트를 위한 시그널

    update_result = QtCore.pyqtSignal(str)  # 크롤링 결과 업데이트를 위한 시그널
    
    error_occurred = QtCore.pyqtSignal(
        str, str
    )  # 오류 발생 시 전송할 시그널 (메시지와 트레이스)

    def __init__(self, url):
        
        # QThread의 초기화 및 추가 변수 초기화
        super().__init__()
        self.url = url  # 크롤링할 URL
        self.results = []  # 크롤링 결과를 저장하기 위한 리스트

    def run(self):
        # QThread의 run() 메서드는 스레드 내에서 실행되는 작업을 정의
        try:
            # ChromeDriverManager를 사용하여 크롬 드라이버 설치
            service = Service(ChromeDriverManager().install())

            # Chrome WebDriver 옵션 설정
            options = webdriver.ChromeOptions()
            options.add_argument(
                "--no-sandbox"
            )  # 리눅스 환경에서 필요한 샌드박스 비활성화 옵션
            options.add_argument("start-maximized")  # 브라우저를 최대화된 상태로 시작

            # WebDriver 객체 생성 및 서비스 시작
            driver = webdriver.Chrome(service=service, options=options)

            # UI 상태 업데이트를 위한 시그널 송신
            self.update_status.emit("페이지 로딩 완료, 크롤링 시작 중...")

            # 지정된 URL로 브라우저 이동
            driver.get(self.url)

            # 첫 번째 XPATH로 span.title 요소 찾기
            try:
                titles = driver.find_elements(By.XPATH, "//span[@class='title']")[
                    :MAX_TITLES
                ]
                if not titles:
                    # 요소가 없는 경우 예외 발생
                    raise NoSuchElementException("span.title 요소를 찾을 수 없습니다.")
            except NoSuchElementException:
                # 첫 번째 XPATH로 찾지 못했을 경우 대체 XPATH 시도
                self.update_status.emit(
                    "span.title 요소를 찾을 수 없어 strong.title로 대체합니다."
                )
                titles = driver.find_elements(By.XPATH, "//strong[@class='title']")[
                    :MAX_TITLES
                ]

            # 찾은 타이틀을 순회하면서 결과 처리
            for i, title in enumerate(titles):
                title_text = title.text  # 각 타이틀의 텍스트 추출
                self.results.append(title_text)  # 결과 리스트에 저장
                # UI에 크롤링 결과 업데이트
                self.update_result.emit(f"제목 {i + 1}: {title_text}\n")
                self.update_status.emit(f"{i + 1}번째 게시글 크롤링 완료")

            # 모든 크롤링 완료 메시지 전송
            self.update_status.emit(
                "크롤링 완료! 저장 버튼을 사용하여 파일에 저장할 수 있습니다."
            )
            driver.quit()  # 브라우저 종료

        except NoSuchElementException as e:

            # 크롤링 요소를 찾지 못했을 때의 예외 처리
            error_trace = traceback.format_exc()  # 예외 정보 가져오기
            self.error_occurred.emit("크롤링 요소를 찾을 수 없습니다.", error_trace)

        except WebDriverException as e:

            # WebDriver 관련 오류 처리
            error_trace = traceback.format_exc()
            self.error_occurred.emit("웹 드라이버 오류 발생.", error_trace)

        except Exception as e:

            # 그 외의 모든 예외 처리
            error_trace = traceback.format_exc()
            self.error_occurred.emit("알 수 없는 오류 발생.", error_trace)


