import logging
import os
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime
from typing import Optional


class Logger:
    def __init__(
        self,
        name: str,
        log_file: str,
        level: int = logging.INFO,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 3,
        max_files: int = 5,
        log_dir: Optional[str] = ".logs",
    ):
        """
        Logger 클래스 생성자.

        Args:
            name (str): 로거 이름.
            log_file (str): 로그 파일 이름.
            level (int): 로그 레벨 (기본값: logging.INFO).
            max_bytes (int): 단일 로그 파일의 최대 크기 (기본값: 5MB).
            backup_count (int): 로그 파일 백업 개수 (기본값: 3).
            max_files (int): 전체 로그 파일 최대 개수 (기본값: 5).
            log_dir (Optional[str]): 로그 파일 저장 디렉토리 (기본값: ".logs").
        """
        self.name = name
        self.level = level
        self.log_dir = log_dir or ".logs"
        self.log_file = self._prepare_log_file_path(log_file)
        self.max_files = max_files

        # Logger 초기화
        self.logger = self._initialize_logger(
            name, self.log_file, level, max_bytes, backup_count
        )

        # 로그 파일 개수 제한 관리
        self._manage_log_files()

    def _prepare_log_file_path(self, log_file: str) -> str:
        """
        로그 파일 경로를 준비.

        Args:
            log_file (str): 기본 로그 파일 이름.

        Returns:
            str: 날짜 및 시간 정보가 포함된 최종 로그 파일 경로.
        """
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name, ext = os.path.splitext(log_file)
        log_file_with_timestamp = f"{base_name}_{current_time}{ext}"

        # 로그 디렉토리 생성
        log_dir_path = os.path.join(self.log_dir, self.name)
        os.makedirs(log_dir_path, exist_ok=True)

        return os.path.join(log_dir_path, log_file_with_timestamp)

    def _initialize_logger(
        self, name: str, log_file: str, level: int, max_bytes: int, backup_count: int
    ) -> logging.Logger:
        """
        로거를 초기화하고 핸들러를 추가.

        Args:
            name (str): 로거 이름.
            log_file (str): 로그 파일 경로.
            level (int): 로그 레벨.
            max_bytes (int): 로그 파일 최대 크기.
            backup_count (int): 백업 로그 파일 개수.

        Returns:
            logging.Logger: 설정된 로거 인스턴스.
        """
        logger = logging.getLogger(name)
        if logger.hasHandlers():  # 이미 핸들러가 설정되어 있으면 초기화하지 않음
            return logger

        logger.setLevel(level)
        logger.propagate = False

        # Formatter 설정
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Stream Handler 추가 (터미널 출력용)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # Rotating File Handler 추가 (파일 출력용)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _manage_log_files(self) -> None:
        """
        로그 파일 개수를 관리하여 초과된 파일 삭제.
        """
        log_dir = os.path.dirname(self.log_file)
        log_files = [
            os.path.join(log_dir, f)
            for f in os.listdir(log_dir)
            if f.endswith(".log")
        ]
        log_files.sort(key=os.path.getmtime)  # 수정 시간 기준 정렬

        # 초과 파일 삭제
        while len(log_files) > self.max_files:
            oldest_file = log_files.pop(0)
            try:
                os.remove(oldest_file)
                self.logger.info(f"Old log file removed: {oldest_file}")
            except OSError as e:
                self.logger.error(f"Failed to remove log file: {oldest_file}. Error: {e}")

    def log_exception(self, message: str, obj: Optional[object] = None) -> None:
        """
        예외 메시지와 객체 정보를 함께 로그를 기록.

        Args:
            message (str): 예외 메시지.
            obj (Optional[object]): 로깅할 객체. 예외(Exception) 또는 사용자 정의 객체.
        """
        if isinstance(obj, Exception):
            # 예외인 경우 exc_info를 활용한 로그
            self.logger.error(f"{message} - Exception: {obj}", exc_info=True)
        elif obj is not None:
            # 사용자 정의 객체를 문자열로 변환하여 출력
            try:
                obj_repr = repr(obj)  # 객체의 문자열 표현을 사용
            except Exception as e:
                obj_repr = f"Failed to retrieve object representation: {e}"
            self.logger.error(f"{message} - Object Info: {obj_repr}")
        else:
            # 단순 메시지 로그
            self.logger.error(message)


    def get_logger(self) -> logging.Logger:
        """
        로거 인스턴스를 반환.

        Returns:
            logging.Logger: 로거 인스턴스.
        """
        return self.logger
