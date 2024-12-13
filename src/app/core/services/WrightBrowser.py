import playwright
from playwright.async_api import Playwright, async_playwright


class WrightBrowser:
    def __init__(self, playwright: Playwright) -> None:

        self._playwright = playwright
        self.browser = None
        self.context = None
        self.page = None

    async def __aenter__(self):
        browser_options = WrightBrowser._get_browser_options()

        if not playwright:
            self._playwright = async_playwright().start()

        self.browser = await self._playwright.chromium.launch(**browser_options)

        self.context = await self.browser.new_context()

        await self.context.set_extra_http_headers(
            {
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }
        )

        self.page = await self.context.new_page()

        await self.page.add_init_script(
            """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """
        )

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        import traceback as tb

        if exc_type:
            print(f"예외 발생: {exc_type.__name__}, {exc_value}")
            print("스택 추적 정보:")
            tb.print_tb(traceback)

        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def goto(self, url: str, timeout: int = 10000):
        import asyncio
        from playwright._impl._errors import Error, TimeoutError

        try:
            await self.page.goto(url, timeout=timeout)
            return True
            # 사용자 행동 모방
            # await self.page.mouse.move(100, 200)  # 마우스 움직임 추가
            # await asyncio.sleep(0.5)  # 적절한 지연 추가

        except TimeoutError:
            self._log(f"페이지 로드 타임아웃: {url}")
        except Error as e:
            if "net::ERR_CONNECTION_RESET" in str(e):
                self._log(f"네트워크 연결이 끊겼습니다: {url}")
            elif "net::ERR_NAME_NOT_RESOLVED" in str(e):
                self._log(f"DNS 문제로 사이트를 찾을 수 없습니다: {url}")
            elif "net::ERR_TIMED_OUT" in str(e):
                self._log(f"네트워크 요청 시간이 초과되었습니다: {url}")
            else:
                self._log(f"Playwright 관련 오류: {str(e)}")
        except Exception as e:
            self._log(f"알 수 없는 오류 발생: {e}")

        return False

    @staticmethod
    def _get_browser_options():
        try:
            headless_mode = False
            executable_path = WrightBrowser._get_browser_path()
            proxy = {
                "server": "http://43.134.68.153:3128",  # 프록시 서버 주소와 포트
            }

            return {
                "headless": headless_mode,
                "proxy": proxy,
                "executable_path": executable_path,
                "args": [
                    "--disable-blink-features=AutomationControlled",  # 자동화 탐지 방지
                    "--no-sandbox",  # 샌드박스 비활성화
                    "--disable-setuid-sandbox",
                    "--disable-infobars",  # 브라우저에 '자동화된 소프트웨어' 알림 비활성화
                    "--disable-dev-shm-usage",  # 공유 메모리 문제 방지
                    "--disable-extensions",  # 확장 프로그램 비활성화
                ],
            }

        except Exception:
            err_msg = f"driver의 browser options을 초기화 중 예외발생!\n"
            WrightBrowser._log(err_msg=err_msg)
            raise

    @staticmethod
    def _get_browser_path():
        from pathlib import Path

        drivers_path = (
            Path.cwd() / "drivers" / "ms-playwright" / "chromium-1140" / "chrome-win"
        )

        browser_path = drivers_path / "chrome.exe"

        if not browser_path.exists():
            err_msg = (
                f"[오류] 'drivers' 디렉토리에서 'chrome.exe' 파일을 찾을 수 없습니다.\n"
                f"현재 경로: {browser_path}"
            )

            WrightBrowser._log(err_msg=err_msg)

            raise FileNotFoundError(err_msg)

        return str(browser_path)

    @staticmethod
    def _log(err_msg="예외!"):
        import traceback as tb
        import os

        print(err_msg)

        tb.print_exc()

        log_folder = "logs"
        os.makedirs(log_folder, exist_ok=True)

        with open(f"{log_folder}/error.log", "w", encoding="utf-8") as f:
            f.write(err_msg + "\n")

            tb.print_exc(file=f)
