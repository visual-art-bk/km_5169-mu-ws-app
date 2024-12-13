import os
import tempfile
import threading
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import shutil
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from app.core.utils.Logger import Logger


class SeniumDravierManager:
    """SeniumDravierManager 클래스
    - 각 요청이 독립적인 Chrome 창을 열도록 설계
    """

    MAX_REQUEST = 10

    logger = Logger(
        name="SeniumDravierManager", log_file="SeniumDravierManager.log"
    ).get_logger()

    def __init__(self, headless=False):
        self.driver = None
        self._request_count = 0  # 요청 횟수
        self._lock = threading.Lock()  # 동시성 제어를 위한 Lock
        self._temp_profile_dir = None  # 임시 프로필 디렉터리
        self.options = {"headless": headless}

    def __enter__(self):

        with self._lock:
            if not self.driver:
                self.driver = self._init_driver()
                if not self.driver:
                    raise RuntimeError("Failed to initialize WebDriver.")
            return self  # self 반환 (manager로 사용)

    def __exit__(self, exc_type, exc_val, exc_tb):

        with self._lock:
            self._quit_driver()

    def _init_driver(self):
        options = self._configure_options()
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def _quit_driver(self):

        if self.driver:
            try:
                self.driver.quit()

            except Exception as e:
                self.logger.error(f"Error quitting WebDriver: {e}")
            finally:
                self.driver = None  # 드라이버 해제

        # 임시 프로필 디렉터리 삭제
        if self._temp_profile_dir and os.path.exists(self._temp_profile_dir):
            try:
                time.sleep(2)  # Chrome 프로세스 종료 대기
                shutil.rmtree(self._temp_profile_dir)

            except Exception as e:
                self.logger.error(f"Error deleting temporary profile directory: {e}")

    def _configure_options(self):
        options = Options()

        if self.options["headless"] == True:
            options.add_argument("--headless")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        # options.add_argument("--blink-settings=imagesEnabled=false")
        
        # options.add_argument("--disable-webgl")  # WebGL 비활성화
        # options.add_argument("--disable-gpu")  # GPU 사용 비활성화
        options.add_argument("--enable-unsafe-swiftshader")  # SwiftShader 강제 사용

        options.page_load_strategy = "normal"

        # 고유한 사용자 데이터 디렉터리 생성
        self._temp_profile_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={self._temp_profile_dir}")

        # 고유한 디버깅 포트 설정
        unique_port = self._get_unique_port()
        options.add_argument(f"--remote-debugging-port={unique_port}")
        self.logger.debug(f"Using unique debugging port: {unique_port}")

        # 사용자 에이전트
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.140 Safari/537.36"
        )
        options.add_argument("--disable-blink-features=AutomationControlled")
        return options

    def _get_unique_port(self):
        """고유한 포트를 생성 (추가 충돌 방지)"""
        base_port = 9222  # 기본 포트 번호
        random_offset = random.randint(1, 1000)  # 1~1000 범위의 랜덤 값
        return base_port + random_offset
