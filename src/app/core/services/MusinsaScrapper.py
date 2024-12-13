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

logger = Logger(name="MusinsaScrapper", log_file="MuScrappe.log").get_logger()


class MusinsaScrapper(SeniumScraper):

    def __init__(self, driver: SeniumDravierManager):

        super().__init__(driver)

        self.kipris_scraper = KiprisScrapper(driver=driver)

        self.event_links = []

        self.tm_state_r_num_list = []  # 등록된상표권출원번호 리스트

        self.tm_state_r_img_srcs: dict[str, dict[str, str]] = (
            {}
        )  # 등록된상표권출원 사진들

        self._scraping_failed_brand_count = 0

    def scrap_all_musinsa_event_link(
        self,
        max_scraping_size=100,
    ):
        link_elems = self.find_all_element(
            by=By.CSS_SELECTOR,
            expression=".newbrand-list__thumbnail a",
            element_description="무신사 이벤트 링크들",
        )

        if len(link_elems) == 0:
            logger.info(
                "저장된 무신사 링크가 없음\n" f"타겟링크 {self.target_link} 확인필요"
            )
            return None

        for elem in link_elems[:max_scraping_size]:
            href = elem.get_attribute("href")
            self.event_links.append(href)

        return self.event_links

    def _goto_target_link(self, link):

        self.driver.execute_script("window.open('');")

        self.driver.switch_to.window(self.driver.window_handles[-1])

        self.driver.get(link)

        self._click_first_prod_thumb(link=link)

        self._drop_down_seller_infos(link_to_debug=link)

        logger.info(f"타겟링크move - {link}")

    def _close_target_link(self, link=""):
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        if link != "":
            logger.info(f"타겟링크close - {link}")

    def scrap(self, link):
        brand_infos = {}
        brand_name = None
        is_brnad_scraping_ok = None
        is_kipris_scraping_ok = None

        try:
            self._goto_target_link(link=link)

        except Exception as e:
            logger.exception(f"타겟링크이동중-예외발생-{link}\n" f"Err: {e}\n")

        try:

            brand_infos = self.scrap_brand_infos(url=link)
            KOR_brand_name = brand_infos["브랜드"]
            EN_brand_name = brand_infos["영문명"]

            tm_prod_codes = self.kipris_scraper.scrap(
                brand_name=KOR_brand_name,
                another_lang_brand_name=EN_brand_name,
            )

            brand_infos["상품분류코드(한)"] = tm_prod_codes

            tm_prod_codes_en_brand_name = self.kipris_scraper.scrap(
                brand_name=EN_brand_name,
                another_lang_brand_name=KOR_brand_name,
            )

            brand_infos["상품분류코드(영)"] = tm_prod_codes_en_brand_name

            is_brnad_scraping_ok = True

        except Exception as e:
            logger.exception(f"타겟브랜드스크래핑중-예외발생\n" f"Err: {e}\n")

        finally:
            self._close_target_link(link=link)
            return brand_infos

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

    def _drop_down_seller_infos(self, link_to_debug):
        did_dropped = False

        self.scroll_page_to_end(sleep=0.25)

        try:
            seller_info_btn = self.find_element(
                by=By.XPATH,
                element_description="셀러정보",
                expression='//div[@data-button-name="판매자정보보기"]',
                timeout=1,
            )

            if seller_info_btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", seller_info_btn
                )

                # 약간의 대기 시간을 추가하여 스크롤이 완료되도록 함
                self.driver.implicitly_wait(0.5)

                seller_info_btn.click()

                did_dropped = True

            # else:
            #     print("셀러 정보 버튼을 찾을 수 없습니다.")

        except ElementClickInterceptedException as e:
            did_dropped = False

            self.log_error(link_to_debug, str(e))
            print("클릭 시 요소가 가려져 있어 예외가 발생했습니다.")
        except Exception as e:
            did_dropped = False

            # 일반적인 예외 처리
            self.log_error(link_to_debug, str(e))
            print("예상치 못한 오류가 발생했습니다:", str(e))
        finally:
            # # 이곳에 예외가 발생해도 실행할 코드를 작성하세요.
            # print(
            #     "_drop_down_seller_infos 메서드 종료"
            # )  # 예외 발생 후에도 진행할 코드 작성

            return did_dropped

    def scrap_brand_infos(self, url):
        # 특정 속성을 가진 div 요소 찾기
        opened_seller_infos = self.find_element(
            by=By.XPATH,
            element_description="열린판매자정보",
            expression='//div[@data-state="open" and @data-orientation="vertical"]',
            timeout=1,
        )

        if opened_seller_infos == None:
            return {}

        # 해당 div 내부의 모든 span 요소 찾기
        span_elements = opened_seller_infos.find_elements(By.TAG_NAME, "span")

        if span_elements == None:
            return {}

        # 모든 정보 키 초기화
        title = None
        infos_list = []

        infos = {
            "상호 / 대표자": None,
            "브랜드": None,
            "사업자번호": None,
            "통신판매업신고": None,
            "연락처": None,
            "E-mail": None,
            "영업소재지": None,
        }

        for index, span in enumerate(span_elements):
            if index % 2 == 0:
                title = span.text
                infos[f"{title}"] = None
                continue

            if index % 2 == 1:
                props_matching_title = span.text
                infos[f"{title}"] = props_matching_title
                continue

        injected_infos = self._inject_data_to_scraped(
            infos=infos,
            list_to_inject=[
                {"브랜드 페이지": url},
                {"영문명": self._extract_brand_name(url=url)},
            ],
        )

        infos_list.append(injected_infos)  # 모든 키가 포함된 infos를 리스트에 추가

        logger.info(
            f"스크래핑완료-타겟브랜드-{infos['브랜드']}\n"
            f"스크래핑완료-타겟링크-{url}\n\n"
        )

        return injected_infos

    @classmethod
    def _extract_brand_name(cls, url):
        # URL을 슬래시(/)로 나눈 후 필요한 부분만 가져오기
        parts = url.split("/")
        brand_name = parts[-2]  # 뒤에서 두 번째 부분이 브랜드 이름
        return brand_name

    @classmethod
    def _inject_data_to_scraped(self, infos: dict, list_to_inject: list):
        try:

            for injecting_info in list_to_inject:
                infos.update(injecting_info)

            return infos
        except Exception as e:
            logger.exception(
                "브랜드 정보리스트에 추가 리스트 주입 중 예외발생\n" f"예외메시지: {e}"
            )
            return None
