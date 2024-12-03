import os
from selenium.webdriver.common.by import By
import time
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook
from selenium.common.exceptions import ElementClickInterceptedException
import json
from selenium import webdriver
from app.core.services.SeniumDravierManager import SeniumDravierManager
from app.core.services.SeniumScraper import SeniumScraper
from app.core.utils import Logger, FileMaker


class MusinsaScrapper(SeniumScraper):
    logger = Logger(
        name="MusinsaScrapper", log_file="logs/services/MuScrappe.log"
    ).get_logger()

    def __init__(self, driver: SeniumDravierManager):

        super().__init__(driver)

        self.event_links = []

        self._scraping_failed_brand_count = 0

    def scrap_all_musinsa_event_link(
        self,
        max_scraping_size=100,
        # max_scroll_attempts=10,
    ):
        link_elems = self.find_all_element(
            by=By.CSS_SELECTOR,
            expression=".newbrand-list__thumbnail a",
            element_description="무신사 이벤트 링크들",
        )

        if len(link_elems) == 0:
            self.logger.info(
                "저장된 무신사 링크가 없음\n" f"타겟링크 {self.target_link} 확인필요"
            )
            return None

        for elem in link_elems[:max_scraping_size]:
            href = elem.get_attribute("href")
            self.event_links.append(href)

        FileMaker.save_list_to_json(list=self.event_links)

        return self.event_links

    def open_link_and_scrap(self, brand_links):
        brands_info_list = []

        for link in brand_links:
            try:

                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])

                self.driver.get(link)

                self._click_first_prod_thumb(link=link)

                self.drop_down_seller_infos(link_to_debug=link)

                scraped = self.scrap_brand_infos(url=link)

                brands_info_list.append(scraped)

            except Exception as e:
                self.logger.exception(
                    f"브랜드 링크에서 스크래핑 중 에러발생:{e}\n" f"링크: {link}"
                )
            finally:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

        return brands_info_list

    def scrap_musinsa_brand_infos_from_json(
        self, link_list=None, json_file_path=None, start_index=0, end_index=None
    ):
        # JSON 파일이 제공되면 JSON 파일에서 링크 리스트를 읽어옴
        if json_file_path:
            with open(json_file_path, "r", encoding="utf-8") as json_file:
                link_list = json.load(json_file)
            print(f"JSON 파일에서 {len(link_list)}개의 링크를 읽어왔습니다.")

        # JSON 파일과 링크 리스트가 모두 없는 경우 에러 처리
        if not link_list:
            raise ValueError("링크 리스트 또는 JSON 파일 경로가 필요합니다.")

        # end_index가 설정된 경우 범위를 벗어나지 않도록 조정
        if end_index is not None:
            if end_index > len(link_list):
                end_index = len(link_list)
            link_list = link_list[start_index:end_index]
        else:
            link_list = link_list[start_index:]

        all_brand_infos = list()

        # 시작점과 종료점 범위 내에서 순회
        for index, link in enumerate(link_list, start=start_index):
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])

            self.driver.get(link)

            try:
                is_clickable = self._click_first_prod_thumb(link=link)
                if not is_clickable:
                    self._scraping_failed_brand_count += 1
                    continue

                is_dropdownable = self.drop_down_seller_infos(link_to_debug=link)
                if not is_dropdownable:
                    self._scraping_failed_brand_count += 1
                    continue

                atomic_infos = self.scrap_brand_infos(link)
                all_brand_infos.append(atomic_infos)  # 전체 리스트에 추가

                print(
                    f"{index + 1 - self._scraping_failed_brand_count}개의 브랜드 정보 저장완료."
                )
                print(f"{self._scraping_failed_brand_count}개의 브랜드 정보 저장실패.")

                # 100개씩 수집될 때마다 저장
                if len(all_brand_infos) % 100 == 0:
                    file_name = f"musinsa_brand_infos_part_{index + 1}.xlsx"
                    self.save_to_excel(all_brand_infos, file_name=file_name)

            except Exception as e:
                self.log_error(link, str(e))  # 에러 발생 시 링크와 메시지 로그에 기록

            finally:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

        # 모든 수집이 끝난 후 최종 저장
        self.save_to_excel(all_brand_infos, file_name="musinsa_brand_infos_full.xlsx")
        return all_brand_infos

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
            #     "drop_down_seller_infos 메서드 종료"
            # )  # 예외 발생 후에도 진행할 코드 작성

            return is_clickable

    def drop_down_seller_infos(self, link_to_debug):
        did_dropped = False
        # self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 자바스크립트를 사용하여 엘리먼트의 위치로 스크롤

        # time.sleep(1)

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
            #     "drop_down_seller_infos 메서드 종료"
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

        # injected_infos_1 = self._inject_data_to_scraped(
        #     info=infos, scrapped_name="브랜드 페이지", scrapped_value=
        # )

        # injected_infos_2 = self._inject_data_to_scraped(
        #     info=injected_infos_1,
        #     scrapped_name="영문명",
        #     scrapped_value=f"{self._extract_brand_name(url=url)}",
        # )

        injected_infos = self._inject_data_to_scraped(
            infos=infos,
            list_to_inject=[
                {"브랜드 페이지": url},
                {"영문명": self._extract_brand_name(url=url)},
            ],
        )
        # scrapped_value_3 = self._scrap_kipris(brand_name=infos["브랜드"])

        # injected_infos_3 = self._inject_data_to_scraped(
        #     info=injected_infos_2,
        #     scrapped_name="키프리스 바로가기",
        #     scrapped_value=scrapped_value_3,
        # )

        infos_list.append(injected_infos)  # 모든 키가 포함된 infos를 리스트에 추가

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
            self.logger.exception(
                "브랜드 정보리스트에 추가 리스트 주입 중 예외발생\n" f"예외메시지: {e}"
            )
            return None

    def _scrap_kipris(self, brand_name):
        try:
            self.driver.get(
                "http://m.kipris.or.kr/mobile/mbl/search/searchResult.mdo#PT_MOVE"
            )

            search_box = self.find_element(
                by=By.CSS_SELECTOR,
                element_description="키프리스-서치박스",
                expression="input[name='searchQuery']",
            )

            search_box.send_keys(brand_name)
            search_box.submit()
            pass
        except Exception as e:
            print(e)

        finally:
            pass
            # self.driver.close()
