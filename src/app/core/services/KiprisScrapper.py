import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.core.services.SeniumDravierManager import SeniumDravierManager
from app.core.services.SeniumScraper import SeniumScraper
from app.core.utils import Logger, FileMaker

logger = Logger(name="KiprisScrapper", log_file="KiprisScrapper.log")


class KiprisScrapper(SeniumScraper):
    _RESULT_NO_MATCH_TM = "상표권출원없음"
    _RESULT_EXECTION_TM = "통신오류"
    _TM_STATE_R = "등록"

    def __init__(self, driver: SeniumDravierManager):
        super().__init__(driver)
        self._base_url = None
        self._target_brand_name = None
        self._another_lang_brand_name = None

    def scrap(
        self,
        brand_name,
        another_lang_brand_name,
        base_url="http://m.kipris.or.kr/mobile/index.jsp",
    ):
        self._base_url = base_url
        self._target_brand_name = brand_name
        self._another_lang_brand_name = another_lang_brand_name
        tm_prod_codes_by_brand_name = {}
        tm_prod_codes = []

        self._goto_kipris_searchbox(brand_name=brand_name, timeout=30)

        self._request_brand_name_in_searchbox(
            brand_name=self._target_brand_name, timeout_for_submit_form=30
        )

        # self.check_page_loading_with_wait(
        #     context="키프리스 서치박스 브랜드네임 검색", timeout=30
        # )

        # self.wait_for_network_idle(timeout=60)

        did_exist_loading_bar = self._check_loading_bar(
            timeout_check_bar=30, timeout_for_loading_bar=30
        )
        if did_exist_loading_bar == None:
            self._close_kipris()
            return KiprisScrapper._RESULT_EXECTION_TM

        tm_tab = self._click_tm_tab(sleep_for_loading=2)

        have_tm_result = self._check_tm(tm_tab=tm_tab)

        if have_tm_result == False:
            self._close_kipris()
            return KiprisScrapper._RESULT_NO_MATCH_TM

        elif have_tm_result == None:
            have_tm_result_in_html = self._check_tm_result_in_html()

            if have_tm_result_in_html == False:
                self._close_kipris()
                return KiprisScrapper._RESULT_NO_MATCH_TM

            elif have_tm_result_in_html == None:
                logger.get_logger().exception(
                    f"브랜드 {self._target_brand_name} 키프리스 검색결과\n"
                )
                logger.get_logger().exception(
                    f"상표권탭=0, 상표권네임을 html소스에서 찾기 모두 예외발생\n"
                )

        tm_elems = self._check_tm_results(brand_name=brand_name)

        if len(tm_elems) == 0:
            self._close_kipris()
            return KiprisScrapper._RESULT_NO_MATCH_TM

        self.scroll_page_to_end(
            max_attempts=100,
            sleep=0.5,
        )

        for tm_el in tm_elems:

            tm_name_el = self._find_tm_name_el(tm_el=tm_el)

            if tm_name_el == None:
                continue

            tm_name = tm_name_el.text
            if self._is_matching_brand_name(tm_name=tm_name) == False:
                continue

            tm_state_el = self._check_tm_state_el(tm_el=tm_el)

            if tm_state_el == None:
                continue

            if KiprisScrapper._TM_STATE_R != tm_state_el.text:
                continue

            tm_pd_code_el = self._find_prod_code_el(tm_el=tm_el)

            if tm_pd_code_el == None:
                continue

            try:
                prod_codes_result = tm_prod_codes_by_brand_name[tm_name]
                prod_codes_result.append(tm_pd_code_el.text)

            except:
                tm_prod_codes.append(tm_pd_code_el.text)
                tm_prod_codes_by_brand_name[tm_name] = tm_prod_codes

        self._close_kipris()

        if len(tm_prod_codes) == 0:
            return KiprisScrapper._RESULT_NO_MATCH_TM

        prod_excel_val = self._convet_prod_codes_to_excel_values(
            codes=tm_prod_codes_by_brand_name
        )
        return f"{prod_excel_val}"

    def check_page_loading_with_wait(self, context, timeout=30):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState")
                == "complete"
            )
            print("페이지 로딩 완료")
        except Exception as e:
            logger.log_exception(message=context, obj=e)

    def wait_for_network_idle(self, timeout=30):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script(
                    "return window.performance.getEntriesByType('resource').filter(e => e.initiatorType === 'xmlhttprequest' || e.initiatorType === 'fetch').length === 0"
                )
            )
            print("모든 네트워크 요청 완료")
        except Exception as e:
            print(f"네트워크 요청 대기 중 오류 발생: {e}")

    def _is_matching_brand_name(self, tm_name: str):
        try:
            # 브랜드 이름 리스트
            brand_names = [
                f"{self._target_brand_name}",
                f"{self._target_brand_name} {self._another_lang_brand_name}",
                f"{self._target_brand_name}{self._another_lang_brand_name}",
                f"{self._another_lang_brand_name}",
                f"{self._another_lang_brand_name} {self._target_brand_name}",
                f"{self._another_lang_brand_name}{self._target_brand_name}",
            ]

            # 대소문자 구별 없이 비교를 위해 입력 텍스트와 브랜드 이름 리스트를 소문자로 변환
            input_text_lower = tm_name.lower()
            brand_names_lower = [name.lower() for name in brand_names]

            # 일치 여부 확인
            return input_text_lower in brand_names_lower
        except Exception as e:
            logger.log_exception(
                message=f"상표권이름를 브랜드이름리스트에서 검사중 // 브랜드-{self._target_brand_name}",
                obj=e,
            )

    def _check_tm(self, tm_tab):
        try:
            tm_result = self.find_element_in_parent(
                parent=tm_tab,
                by=By.TAG_NAME,
                element_description="상표권존재유무체크",
                expression="span",
            ).text

            if tm_result != "0":
                return True
            else:
                logger.get_logger().info(
                    f"{self._target_brand_name} 에 대한 키프리스검색결과없음\n"
                )
                return False
        except Exception as e:
            logger.log_exception(
                message=f"출원하거나 등록한 상표권 리스트체크 // 브랜드-{self._target_brand_name}",
                obj=e,
            )
            return None

    def _check_tm_result_in_html(self):
        try:
            html_source = self.driver.page_source

            search_text = "검색결과가 없습니다"
            if search_text in html_source:
                print(f"텍스트 '{search_text}'가 페이지에 존재합니다.")
                return True
            else:
                print(f"텍스트 '{search_text}'가 페이지에 존재하지 않습니다.")
                return False
        except Exception as e:
            logger.log_exception(
                message=f"상표권출원정보결과를 html페이지소스에서 찾는중 // 브랜드-{self._target_brand_name}",
                obj=e,
            )
            return None

    def _find_prod_code_el(self, tm_el):
        try:
            scraped_tm_category_codes = self.find_element_in_parent(
                parent=tm_el,
                by=By.CSS_SELECTOR,
                element_description="상품분류코드들",
                expression="ul > li:nth-child(2) > span",
                timeout=5,
            )

            return scraped_tm_category_codes

        except Exception as e:
            logger.log_exception(message="상품분류코드 찾는중", obj=e)
            return None

    def _check_tm_state_el(self, tm_el):
        try:
            tm_state_el = self.find_element_in_parent(
                parent=tm_el,
                by=By.CSS_SELECTOR,
                element_description="상표권등록상태여부",
                expression="span.state",
                timeout=5,
            )
            return tm_state_el

        except Exception as e:
            logger.log_exception(
                message=f"상표권등록상태여부 검사중 // 브랜드-{self._target_brand_name}",
                obj=e,
            )
            return None

    def _find_tm_name_el(self, tm_el):

        try:
            tm_name_el = self.find_element_in_parent(
                parent=tm_el,
                by=By.CSS_SELECTOR,
                element_description=f"브랜드네임과 상표권매칭중 // 브랜드-{self._target_brand_name}",
                expression="a",
                timeout=2,
            )

            return tm_name_el

        except Exception as e:
            logger.log_exception(
                message=f"브랜드네임과 상표권매칭중 // 브랜드-{self._target_brand_name}",
                obj=e,
            )
            return None

    def _goto_kipris_searchbox(self, brand_name, timeout=10):
        try:
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])

            # 키프리스 페이지로 이동
            self.driver.get("http://m.kipris.or.kr/mobile/index.jsp")

        except Exception as e:
            logger.log_exception(
                message=f"키프리스-서치박스 입력이동중 // 브랜드-{self._target_brand_name}",
                obj=e,
            )

    def _request_brand_name_in_searchbox(self, brand_name, timeout_for_submit_form=30):
        try:
            # 서치박스 찾기 및 검색어 입력
            search_box = self.find_element(
                by=By.CSS_SELECTOR,
                element_description=f"{brand_name} 키프리스-서치박스 검색",
                expression="input[name='searchQuery']",
                timeout=timeout_for_submit_form,
            )
            search_box.send_keys(self._target_brand_name)
            search_box.submit()

        except Exception as e:
            logger.log_exception(
                message=f"키프리스-서치박스 검색중 // 브랜드-{brand_name}",
                obj=e,
            )

    def _close_kipris(self):
        try:

            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        except Exception as e:
            logger.log_exception(
                message=f"키프리스 탭 닫는중 // 브랜드-{self._target_brand_name}", obj=e
            )

    def _check_loading_bar(self, timeout_check_bar=3, timeout_for_loading_bar=30):
        try:
            # loading-bar 존재 여부 확인
            loading_bar_present = False
            try:
                # 요소가 존재하는지 확인 (최대 3초 대기)
                WebDriverWait(self.driver, timeout=timeout_check_bar).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.loading-bar"))
                )
                loading_bar_present = True
            except TimeoutException:
                print("Loading bar is not present. Proceeding without wait.")

                return None

            # loading-bar가 존재하면 비가시 상태가 될 때까지 대기
            if loading_bar_present:
                logger.get_logger().info(
                    f"로딩바가 존재 완료할때까지 {timeout_for_loading_bar} 대기 // 브랜드-{self._target_brand_name}"
                )

                WebDriverWait(self.driver, timeout=timeout_for_loading_bar).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, "div.loading-bar")
                    )
                )
                logger.get_logger().info(
                    f"로딩바 로딩완료 display:none으로 숨김처리됨 // 브랜드-{self._target_brand_name}"
                )

            else:
                logger.get_logger().info(
                    f"로딩바가 존재하지 않음 // 브랜드-{self._target_brand_name}"
                )

            return True
        except TimeoutException:
            logger.get_logger().exception(
                "로딩바 대기 timeoue {timeout_for_loading_bar}초"
            )

            return None

    def _click_tm_tab(self, sleep_for_loading=3):
        time.sleep(sleep_for_loading)

        try:
            # 키프리스 상표 탭 클릭
            # JavaScript로 버튼 강제 클릭
            tm_tab = self.find_element(
                by=By.CSS_SELECTOR,
                expression="button#TM",
                element_description="키프리스 상표 탭",
                timeout=60,
            )
            self.driver.execute_script("arguments[0].click();", tm_tab)
            return tm_tab
        except Exception as e:
            logger.log_exception(
                message=f"키프리스-상표권탭클릭 // 브랜드-{self._target_brand_name}",
                obj=e,
            )
            return None

    def _check_tm_results(self, brand_name):
        tm_elems = []

        try:
            tm_elems = self.find_all_element(
                by=By.CSS_SELECTOR,
                expression="#tmResult .row .content-data-text",
                element_description="상표권출원신청그룹",
            )

        except Exception as e:
            logger.log_exception(
                message=f"브랜드{brand_name}-상표권출원신청그룹찾는중", obj=e
            )
            return []

        finally:
            return tm_elems

    def _convet_prod_codes_to_excel_values(self, codes: dict):
        try:
            excel_vals = []

            for tm_name, prod_codes in codes.items():

                sorted_nums = sorted(prod_codes)

                refine_prod_code = ", ".join(sorted_nums)
                refine_code = f"{tm_name}-{refine_prod_code}"
                excel_vals.append(refine_code)

            return " // ".join(excel_vals)
        except Exception as e:
            logger.log_exception(
                message=f"추출한상품코드를 문자열로 변환중 예외발생 // 브랜드-{self._target_brand_name}",
                obj=e,
            )
            return "KiprisScrapper-문자열변환오류"
