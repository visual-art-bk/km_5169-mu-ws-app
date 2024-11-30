import sys
import traceback
import datetime
from PyQt5 import QtWidgets, QtGui, QtCore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from app.ui.CrawlerUI import CrawlerUI

def main():
    # PyQt5 애플리케이션 초기화 및 실행
    app = QtWidgets.QApplication(sys.argv)  # QApplication 객체 생성

    ex = CrawlerUI()  # CrawlerUI 객체 생성 및 실행

    ex.show()  # UI 표시
    
    sys.exit(app.exec_())  # 이벤트 루프 실행 및 종료 처리


if __name__ == "__main__":
    main()  # 스크립트가 직접 실행될 경우 main() 함수 호출
