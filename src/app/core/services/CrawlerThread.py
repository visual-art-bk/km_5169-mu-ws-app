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
from app.core.services.KiprisScrapper import KiprisScrapper


class CrawlerThread(QtCore.QThread):
    update_status = QtCore.Signal(str)
    update_result = QtCore.Signal(str)
    update_progress = QtCore.Signal(int)  # 크롤링된 브랜드 수 전달
    error_occurred = QtCore.Signal(str, str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.results = []
        self.scraper = None
        self.kipris_scraper = None
        self.max_scraping_size = 50  # 기본값 설정

    def run(self):
        try:
            # max_scroll_attempts를 max_scraping_size의 비율에 따라 계산
            max_scroll_attempts = max(5, self.max_scraping_size // 10)

            with SeniumDravierManager(headless=False) as manager:
                driver = manager.driver
                self.scraper = MusinsaScrapper(driver=driver)

                self.scraper.goto(url=self.url)

                self.scraper.scroll_with_more_btn(
                    by=By.XPATH,
                    expression='//button[@data-button-name="더보기"]',
                    sleep_for_loading=1,
                    max_scroll_attempts=max_scroll_attempts,
                    timeout=10,
                )

                event_links = self.scraper.scrap_all_musinsa_event_link(
                    max_scraping_size=self.max_scraping_size
                )

                brands_info_list = []
                for i, link in enumerate(event_links):
                    brand_info = self.scraper.scrap(link=link)
                    brands_info_list.append(brand_info)
                    self.update_progress.emit(len(brands_info_list))

                self.results = brands_info_list

        except WebDriverException as e:
            error_trace = traceback.format_exc()
            self.error_occurred.emit("웹 드라이버 오류 발생.", error_trace)

        except Exception as e:
            error_trace = traceback.format_exc()
            self.error_occurred.emit("알 수 없는 오류 발생.", error_trace)
