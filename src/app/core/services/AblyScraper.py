import re
import os
from selenium.webdriver.common.by import By
import time
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    InvalidArgumentException,
)
import json
from selenium import webdriver
from app.core.services.SeniumDravierManager import SeniumDravierManager
from app.core.services.SeniumScraper import SeniumScraper
from app.core.utils import Logger, FileMaker
from app.core.utils.ImgMaker import save_imgs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .KiprisScrapper import KiprisScrapper
from bs4 import BeautifulSoup
import requests

logger = Logger(name="AblyScraper", log_file="AblyScraper.log").get_logger()


class AblyScraper(SeniumScraper):

    def __init__(self, driver: SeniumDravierManager):

        super().__init__(driver)

        self.kipris_scraper = KiprisScrapper(driver=driver)

        self.event_links = []

        self.tm_state_r_num_list = []  # 등록된상표권출원번호 리스트

        self.tm_state_r_img_srcs: dict[str, dict[str, str]] = (
            {}
        )  # 등록된상표권출원 사진들

        self._scraping_failed_brand_count = 0

        self._market_infos = {}

    def _go_cloth_section(self):
        try:
            self.find_element(
                by=By.CSS_SELECTOR,
                element_description="의류섹션",
                expression='img[alt="의류"]',
                timeout=30,
            ).click()
        except Exception as e:
            logger.exception("의류섹션 클릭 - {e}")

    def _scrape_recomended_item_links(
        self,
        current_recomended_item_index,
        recomended_item_links: list = [],
        max_scraping_size=100,
    ):
        try:
            link_elems = self.find_all_element(
                by=By.XPATH,
                expression="//p[contains(text(), '구매중')]",
                element_description="에이블리 의류섹션 추천아이템링크들",
            )

            len_link_elmes = len(link_elems)
            if len_link_elmes == 0:
                logger.info(
                    "발견된 추천링크가 없음\n" f"타겟링크 {self.target_link} 확인필요"
                )
                return None

            logger.info(f"발견된 추천 아이템 개수:{len_link_elmes}")

            for i, elem in enumerate(link_elems[:max_scraping_size]):
                if current_recomended_item_index != i:
                    continue

                self.scroll_element_into_view_center(elem)

                elem.click()

                WebDriverWait(self.driver, 30).until(lambda d: "goods" in d.current_url)

                current_url = self.driver.current_url

                recomended_item_links.append(current_url)

            return current_url
        except Exception as e:
            logger.exception("에이블리 의류섹션 추천아이템링크들 스크래핑중 - {e}")
            return []

    def _scrap_market_link(self, recomended_item_url):
        """
        에이블리의 차단 정책때문에 현재 AblyScraper에서는 필요한 스크랩 구간에서
        브라우저를 open과 close를 반복하고 있다.
        이 함수는 market_link를 스크랩 후, 에이블리의 차단이 없으면 market_name을
        스크랩 한다.
        """
        try:
            with SeniumDravierManager(headless=True) as manager:
                _driver = manager.driver

                self.driver = _driver

                self.driver.get(recomended_item_url)

                market_img_elem = self.find_element(
                    by=By.CSS_SELECTOR, expression='picture > img[alt="마켓 이미지"]'
                )

                self.scroll_element_into_view_center(target=market_img_elem)

                if market_img_elem == None:
                    return None

                market_img_elem.click()

                WebDriverWait(self.driver, 30).until(
                    lambda d: "markets" in d.current_url
                )
                print(f"찾은 마켓 링크 URL: {self.driver.current_url}")

                return self.driver.current_url

        except InvalidArgumentException as e:
            logger.exception("마켓링크 스크래핑 - {e}\n")
            logger.exception(f"예외발생 url - {self.driver.current_url}")
            return None
        except Exception as e:
            logger.exception("마켓링크 스크래핑 - {e}\n")
            logger.exception(f"예외발생 url - {self.driver.current_url}")
            return None

    def _scrap_market_infos(self, recomended_item_url):
        try:
            market_link = self._scrap_market_link(recomended_item_url)

            if market_link == None:
                return {}
            else:
                self._market_infos["브랜드 페이지"] = market_link

            market_info_link = AblyScraper.convert_url(market_link)

            # 에이블리의 차단프로그램 때문에, 브라우저를 닫고 다시 열어서 진행
            with SeniumDravierManager(headless=True) as manager:
                _driver = manager.driver

                self.driver = _driver

                self.driver.get(market_info_link)

                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "p"))
                )

                company_name = self._scrap_seller_info(keyword="상호:")
                company_CEO_name = self._scrap_seller_info(keyword="대표자:")
                self._market_infos["상호 / 대표자"] = (
                    f"{company_name} / {company_CEO_name}"
                )

                self._market_infos["브랜드"] = self._scrap_seller_info(
                    keyword="마켓 정보", cut_after=False
                )
                self._market_infos["사업자번호"] = self._scrap_seller_info(
                    keyword="사업자등록번호:"
                )
                self._market_infos["통신판매업신고"] = self._scrap_seller_info(
                    keyword="통신판매업신고번호:"
                )
                self._market_infos["연락처"] = self._scrap_seller_info(
                    keyword="전화번호:"
                )
                self._market_infos["E-mail"] = self._scrap_seller_info(
                    keyword="이메일:"
                )
                self._market_infos["영업소재지"] = self._scrap_seller_info(
                    keyword="주소:"
                )
                self._market_infos["영문명"] = "고객요청으로추출X"

        except Exception as e:
            logger.exception(f"마켓 정보 스크래핑중 - {e}")

        finally:
            self.driver.quit()
            return self._market_infos

    def _scrape_prod_codes_on_kipris(self, market_infos: dict):
        KOR_brand_name = self._market_infos["브랜드"]
        EN_brand_name = None

        with SeniumDravierManager(headless=True) as manager:

            _driver = manager.driver

            self.kipris_scraper.driver = _driver

            self._market_infos["상품분류코드(한)"] = self.kipris_scraper.scrap(
                brand_name=KOR_brand_name,
                another_lang_brand_name=EN_brand_name,
            )
            self._market_infos["상품분류코드(영)"] = "고객요청으로추출X"

            return self._market_infos

    def _scrap_seller_info(self, keyword, cut_after=True):
        try:
            seller_info_el = self.find_element(
                by=By.XPATH,
                expression=f"//p[contains(text(), '{keyword}')]",
                element_description="브랜드 인포-대표자",
            )

            if seller_info_el == None:
                return "스크랩실패"

            seller_info_chunk = seller_info_el.text
            return AblyScraper.process_reg_expression(
                flag_word=keyword,
                chunk_target_word=seller_info_chunk,
                cut_after=cut_after,
            )

        except Exception as e:
            logger.exception(f"{keyword} 이름 스크래핑 - {e}")

    @staticmethod
    def process_reg_expression(flag_word, chunk_target_word, cut_after=True):
        """
        주어진 flag_word를 기준으로 텍스트를 자릅니다.
        :param flag_word: 기준 단어
        :param chunk_target_word: 대상 텍스트
        :param cut_after: True면 flag_word 뒤 텍스트 추출, False면 flag_word 앞 텍스트 추출
        :return: 자른 결과 문자열
        """
        if cut_after:
            # flag_word 뒤의 텍스트 추출
            pattern = rf"{flag_word}\s*(.+)"
        else:
            # flag_word 앞의 텍스트 추출
            pattern = rf"(.+?)\s*{flag_word}"

        match = re.search(pattern, chunk_target_word)
        if match:
            return match.group(1).strip()
        return f"정규화작업실패-{chunk_target_word}"

    @staticmethod
    def convert_url(url):
        """
        a-bly.com URL을 m.a-bly.com URL로 변환하는 함수
        :param url: str - 원본 URL
        :return: str - 변환된 URL
        """
        if "a-bly.com/app/markets/" in url:
            # 변환 로직
            market_id = url.split("a-bly.com/app/markets/")[-1]
            return f"https://m.a-bly.com/market/{market_id}/info"
        else:
            raise ValueError("올바른 a-bly.com/app/markets/ URL이 아닙니다.")

    def _goto_kipris_searchbox(self, brand_name):
        try:
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])

            # 키프리스 페이지로 이동
            self.driver.get("http://m.kipris.or.kr/mobile/index.jsp")

            time.sleep(1.5)

            # 서치박스 찾기 및 검색어 입력
            search_box = self.find_element(
                by=By.CSS_SELECTOR,
                element_description="키프리스-서치박스",
                expression="input[name='searchQuery']",
            )
            search_box.send_keys(brand_name)
            search_box.submit()

        except Exception as e:
            logger.exception(
                f"키프리스링크서치박스-이동중-예외발생-브랜드 {brand_name}\n"
                f"Err: {e}"
            )

    def _close_kipris(self):
        # 새 탭 닫기 및 원래 탭으로 돌아가기
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def _click_tm_tab(self, sleep_for_loading=3):
        time.sleep(sleep_for_loading)

        try:
            # 키프리스 상표 탭 클릭
            # JavaScript로 버튼 강제 클릭
            tm_tab = self.find_element(
                by=By.CSS_SELECTOR,
                expression="button#TM",
                element_description="키프리스 상표 탭",
                timeout=5,
            )
            self.driver.execute_script("arguments[0].click();", tm_tab)
            return tm_tab
        except Exception as e:
            logger.exception(f"키프리스-상표권탭클릭-예외발생!\n" f"Err: {e}\n")
            return None

    def _click_first_prod_thumb(self, link):
        is_clickable = False

        try:

            thumb = self.find_element(
                by=By.CSS_SELECTOR,
                element_description="첫번째상품썸네일",
                expression="a.new-brand__goods-item",
            )

            if thumb == None:
                is_clickable = False
                # return is_clickable

                # 자바스크립트를 사용하여 엘리먼트의 위치로 스크롤
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", thumb
            )

            # 약간의 대기 시간을 추가하여 스크롤이 완료되도록 함
            self.driver.implicitly_wait(0.5)

            thumb.click()
            is_clickable = True

        except ElementClickInterceptedException as e:
            is_clickable = False

            self.log_error(link, str(e))
            print("클릭 시 요소가 가려져 있어 예외가 발생했습니다.")

        except Exception as e:
            is_clickable = False

            # 일반적인 예외 처리
            self.log_error(link, str(e))
            print("예상치 못한 오류가 발생했습니다:", str(e))
        finally:
            # # 이곳에 예외가 발생해도 실행할 코드를 작성하세요.
            # print(
            #     "_drop_down_seller_infos 메서드 종료"
            # )  # 예외 발생 후에도 진행할 코드 작성

            return is_clickable
