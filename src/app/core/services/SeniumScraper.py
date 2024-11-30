import traceback
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from contextlib import contextmanager
from app.core.utils.Logger import Logger

MAX_REQUEST = 10


class WebScarper:

    logger = Logger(
        name="WebScarper", log_file="logs/services/WebScarper.log"
    ).get_logger()

    def __init__(self, driver: webdriver.Chrome, timeout):
        super().__init__(driver, timeout)
        self.driver = driver

    def goto(self, url):

        self.driver.get(url)
        self.driver.maximize_window()

    def search_keyword_in_form(self, keyword, by, expression):
        if not keyword:
            raise ValueError("ValueError - 검색에 사용되는 키워드 입력은 필수")

        WebScarper._validate_selenium_input(
            by=by, expression=expression, context="검색"
        )

        try:
            search_box = self.find_element(
                by=by,
                expression=expression,
                element_description="검색창 폼",
            )
            if not search_box:
                self.logger(f"{expression} 에 해당하는 검색창 폼 엘리멘트 없음")
                return False

            search_box.send_keys(keyword)
            search_box.submit()
            return True

        except Exception as e:
            self.logger.exception(
                f"{expression} 을 사용한 검색창 폼에 키웓드 검색에서 예외 발생"
            )
            return False

    def find_element(
        self,
        by,
        expression="정의되지않음",
        element_description="정의되지않은-엘레멘트",
        timeout=10,
    ):
        WebScarper._validate_selenium_input(
            by=by, expression=expression, context="검색"
        )

        try:

            element = WebDriverWait(self.driver, timeout=timeout).until(
                EC.presence_of_element_located((by, expression))
            )

            if not element:
                self.logger.info(f"{expression} 에 해당되는 엘리멘트 없음")
                return None

            return element

        except Exception as e:
            self.logger.exception(f"{expression} 에 매칭되는 엘리멘트 찾는 중 예외발생")

            return None

    def find_all_element(
        self,
        by,
        expression="정의되지않음",
        element_description="multiple element정의되지않은-엘레멘트들",
        timeout=10,
    ):
        WebScarper._validate_selenium_input(
            by=by, expression=expression, context="검색"
        )

        try:

            elements = WebDriverWait(self.driver, timeout=timeout).until(
                EC.presence_of_all_elements_located((by, expression))
            )

            if not elements:
                self.logger.info(f"{expression} 에 해당되는 엘리멘트들 없음")
                return None

            return elements
        except Exception as e:

            self.logger.exception(
                f"{expression} 에 매칭되는 엘리멘트들을 찾는 중 예외발생"
            )

            return None

    @contextmanager
    def switch_to_iframe(self, timeout=10):
        """
        주어진 iframe으로 전환하고, 작업 완료 후 기본 컨텍스트로 복귀하는 함수.
        :param iframe_locator: iframe을 찾기 위한 Selenium By locator (예: (By.ID, "iframe-id"))
        :param timeout: iframe 탐색 대기 시간 (기본값: 10초)
        """
        try:

            iframe = self.find_element(
                by=By.CSS_SELECTOR, element_description="iframe", expression="iframe"
            )

            if not iframe:
                return False

            self.driver.switch_to.frame(iframe)

            self.logger.info(f"iframe 전환 성공")

            yield

        finally:
            if iframe:

                self.driver.switch_to.default_content()
                self.logger.info("iframe에서 복귀")
                return True
            return False

    @staticmethod
    def _validate_selenium_input(by, expression, context="검색"):
        if not by:
            raise ValueError(
                f"ValueError - {context}에 사용되는 'by'는 필수입니다."
                f" 예: By.CSS_SELECTOR"
            )
        if not expression:
            raise ValueError(
                f"ValueError - {context}에 사용되는 'expression'은 필수입니다."
                f" 예: input[@name='query']"
            )
