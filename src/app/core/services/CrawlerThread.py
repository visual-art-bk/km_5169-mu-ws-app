import time
import sys
import traceback
import datetime
from PySide6 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from app.core.services.SeniumDravierManager import SeniumDravierManager
from app.core.services.MusinsaScrapper import MusinsaScrapper


class CrawlerThread(QtCore.QThread):
    # PySide6 Signal 정의: UI 업데이트를 위해 필요한 정보를 전송
    update_status = QtCore.Signal(str)  # 상태 메시지 업데이트를 위한 시그널
    update_result = QtCore.Signal(str)  # 크롤링 결과 업데이트를 위한 시그널
    error_occurred = QtCore.Signal(
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
            # Selenium 드라이버 관리
            with SeniumDravierManager(headless=True) as manager:
                driver = manager.driver

                # MusinsaScrapper 초기화
                self.scraper = MusinsaScrapper(driver=driver)

                # URL 이동
                self.scraper.goto(url=self.url)

                # "더보기" 버튼 클릭으로 스크롤링
                self.scraper.scroll_with_more_btn(
                    by=By.XPATH,
                    expression='//button[@data-button-name="더보기"]',
                    sleep_for_loading=1,
                    max_scroll_attempts=10,
                    timeout=10,
                )

                # 이벤트 링크 스크래핑
                event_links = self.scraper.scrap_all_musinsa_event_link(
                    max_scraping_size=100
                )

                # 브랜드 정보 수집
                brands_info_list = self.scraper.open_link_and_scrap(
                    brand_links=event_links
                )

                # 결과 저장
                self.results = brands_info_list

        except WebDriverException as e:
            # WebDriver 관련 오류 처리
            error_trace = traceback.format_exc()
            self.error_occurred.emit("웹 드라이버 오류 발생.", error_trace)

        except Exception as e:
            # 그 외의 모든 예외 처리
            error_trace = traceback.format_exc()
            self.error_occurred.emit("알 수 없는 오류 발생.", error_trace)
