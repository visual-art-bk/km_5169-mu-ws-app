import time
import sys
import traceback
import datetime
from PyQt5 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from app.core.services.SeniumDravierManager import SeniumDravierManager
from app.core.services.MusinsaScrapper import MusinsaScrapper

START_TIME = datetime.datetime(2024, 11, 30, 00, 30)  # 샘플 사용 시작 시간
LIMIT_TIME = datetime.timedelta(minutes=3600)  # 사용 가능한 제한 시간 설정
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
        self.scraper = None

    def run(self):
        try:
            with SeniumDravierManager(headless=False) as manager:
                driver = manager.driver

                self.scraper = MusinsaScrapper(driver=driver)

                self.scraper.goto(url=self.url)
                
                event_links = self.scraper.scrap_all_musinsa_event_link(
                    max_scraping_size=110,
                    max_scroll_attempts=10
                )

                if event_links:
                    print(event_links)


                time.sleep(10)

        except WebDriverException as e:
            # WebDriver 관련 오류 처리
            error_trace = traceback.format_exc()
            self.error_occurred.emit("웹 드라이버 오류 발생.", error_trace)

        except Exception as e:

            # 그 외의 모든 예외 처리
            error_trace = traceback.format_exc()
            self.error_occurred.emit("알 수 없는 오류 발생.", error_trace)
