import time
import sys
import traceback
import datetime
from PySide6 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from app.core.services.SeniumDravierManager import SeniumDravierManager
from app.core.services.AblyScraper import AblyScraper
from app.core.services.KiprisScrapper import KiprisScrapper
from app.core.utils.Logger import Logger

logger = Logger(name="AblyThread", log_file="AblyThread.log").get_logger()


class AblyThread(QtCore.QThread):
    update_status = QtCore.Signal(str)
    update_result = QtCore.Signal(str)
    update_progress = QtCore.Signal(int)  # 크롤링된 브랜드 수 전달
    error_occurred = QtCore.Signal(str, str)

    def __init__(self, url="https://m.a-bly.com/"):
        super().__init__()
        self.url = url
        self.results = []
        self.cookies = []
        self.scraper = None
        self.kipris_scraper = None
        self.max_scraping_size = 50  # 기본값 설정
        self.recomended_item_links = []
        self.current_recomended_item_index = 0
        self.max_scroll_attempts = 0
        self._market_info_list = []

    def run(self):
        try:
            # max_scroll_attempts를 max_scraping_size의 비율에 따라 계산
            self.max_scroll_attempts = max(5, ((self.max_scraping_size // 10)) - 2)

            for i in range(self.max_scraping_size):
                clicked_item_url = self._scrap_recomended_item_link(
                    max_scroll_attempts=self.max_scroll_attempts
                )
                if clicked_item_url == None:
                    logger.warning("에이블리의류 섹션에서 상품(아이템)링크 스크랩실패")
                    continue

                market_infos = self.scraper._scrap_market_infos(clicked_item_url)

                if len(market_infos) == 0:
                    continue

                market_info_add_prod_codes = self.scraper._scrape_prod_codes_on_kipris(
                    market_infos=market_infos
                )

                self._market_info_list.append(market_info_add_prod_codes)
                self.update_progress.emit(len(self._market_info_list))

            self.results = self._market_info_list

        except WebDriverException as e:
            error_trace = traceback.format_exc()
            self.error_occurred.emit("웹 드라이버 오류 발생.", error_trace)

        except Exception as e:
            error_trace = traceback.format_exc()
            self.error_occurred.emit("알 수 없는 오류 발생.", error_trace)

    def _scrap_recomended_item_link(self, max_scroll_attempts=5):
        clicked_item_url = None
        try:
            with SeniumDravierManager(headless=True) as manager:
                driver = manager.driver
                self.scraper = AblyScraper(driver=driver)

                self.scraper.goto(url=self.url)

                self.scraper._go_cloth_section()

                time.sleep(1)

                self.scraper.scroll_page_to_end(
                    sleep=1, max_attempts=self.max_scroll_attempts
                )

                clicked_item_url = self.scraper._scrape_recomended_item_links(
                    max_scraping_size=self.max_scraping_size,
                    current_recomended_item_index=self.current_recomended_item_index,
                    recomended_item_links=self.recomended_item_links,
                )

                self.current_recomended_item_index += 1
                print(f"현재 모든 추천 아이템 링크들: {self.recomended_item_links}")

        except Exception as e:
            print(e)

        finally:
            self.scraper.driver.quit()
            return clicked_item_url
