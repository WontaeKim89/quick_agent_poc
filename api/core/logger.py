import logging
import os
import sys
from api.core.singleton import Singleton
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """컬러 출력을 위한 커스텀 포맷터"""

    # ANSI 컬러 코드
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, *args, use_colors=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors and sys.stderr.isatty()

    def format(self, record):
        if self.use_colors:
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = (
                    f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"
                )
                record.msg = f"{self.COLORS[levelname]}{record.msg}{self.RESET}"
        return super().format(record)


class APILogger(Singleton):
    def __init__(self):
        self.logger = logging.getLogger("APILogger")
        self.appinsights_handler: Optional[object] = None

        # 환경변수로 로그 레벨 설정
        # LOG_LEVEL=DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        self.logger.propagate = False

        # 콘솔 로그 레벨 설정
        console_level = os.getenv("CONSOLE_LOG_LEVEL", log_level).upper()

        # 컬러 출력 설정 (환경변수로 제어)
        use_colors = os.getenv("LOG_COLORS", "true").lower() == "true"

        if not self.logger.handlers:

            # 콘솔 핸들러
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(getattr(logging, console_level, logging.INFO))

            # 콘솔용 포맷터 (컬러 지원)
            console_format = "[%(asctime)s] [%(levelname)-8s] %(message)s"
            if os.getenv("ENVIRONMENT", "local") == "local":
                # 로컬 환경에서는 더 간단한 포맷 사용
                console_format = "[%(levelname)-8s] %(message)s"

            stream_fmt = ColoredFormatter(
                console_format, "%H:%M:%S", use_colors=use_colors
            )
            stream_handler.setFormatter(stream_fmt)
            self.logger.addHandler(stream_handler)

            # Application Insights 핸들러 추가
            self._setup_application_insights()

    def set_level(self, level: str):
        """런타임에 로그 레벨 변경"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # 콘솔 핸들러 레벨도 업데이트
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                # Application Insights 핸들러가 아닌 경우에만 레벨 변경
                if not hasattr(handler, '__class__') or 'Azure' not in handler.__class__.__name__:
                    handler.setLevel(log_level)

    def set_console_level(self, level: str):
        """콘솔 출력 레벨만 변경"""
        console_level = getattr(logging, level.upper(), logging.INFO)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                # Application Insights 핸들러가 아닌 경우에만 레벨 변경
                if not hasattr(handler, '__class__') or 'Azure' not in handler.__class__.__name__:
                    handler.setLevel(console_level)


    def debug(self, msg, extra_data=None, **kwargs):
        """DEBUG 레벨 로그 with Application Insights custom properties support"""
        extra = {}
        if extra_data and isinstance(extra_data, dict):
            # 파일/콘솔 로그에는 추가 데이터를 문자열로 표시
            display_msg = f"{msg} | {extra_data}"
            # Application Insights에는 custom_dimensions로 전달
            extra["custom_dimensions"] = extra_data
        else:
            display_msg = msg

        # kwargs에서 추가 custom dimensions 병합
        if kwargs:
            extra.setdefault("custom_dimensions", {}).update(kwargs)

        self.logger.debug(
            display_msg if extra_data else msg, extra=extra if extra else None
        )

    def info(self, msg, extra_data=None, **kwargs):
        """INFO 레벨 로그 with Application Insights custom properties support"""
        extra = {}
        if extra_data and isinstance(extra_data, dict):
            display_msg = f"{msg} | {extra_data}"
            extra["custom_dimensions"] = extra_data
        else:
            display_msg = msg

        if kwargs:
            extra.setdefault("custom_dimensions", {}).update(kwargs)

        self.logger.info(
            display_msg if extra_data else msg, extra=extra if extra else None
        )

    def warning(self, msg, extra_data=None, **kwargs):
        """WARNING 레벨 로그 with Application Insights custom properties support"""
        extra = {}
        if extra_data and isinstance(extra_data, dict):
            display_msg = f"{msg} | {extra_data}"
            extra["custom_dimensions"] = extra_data
        else:
            display_msg = msg

        if kwargs:
            extra.setdefault("custom_dimensions", {}).update(kwargs)

        self.logger.warning(
            display_msg if extra_data else msg, extra=extra if extra else None
        )

    def error(self, msg, exc_info=False, extra_data=None, **kwargs):
        """ERROR 레벨 로그 with Application Insights custom properties support"""
        extra = {}
        if extra_data and isinstance(extra_data, dict):
            display_msg = f"{msg} | {extra_data}"
            extra["custom_dimensions"] = extra_data
        else:
            display_msg = msg

        if kwargs:
            extra.setdefault("custom_dimensions", {}).update(kwargs)

        self.logger.error(
            display_msg if extra_data else msg,
            exc_info=exc_info,
            extra=extra if extra else None,
        )

    def critical(self, msg, extra_data=None, **kwargs):
        """CRITICAL 레벨 로그 with Application Insights custom properties support"""
        extra = {}
        if extra_data and isinstance(extra_data, dict):
            display_msg = f"{msg} | {extra_data}"
            extra["custom_dimensions"] = extra_data
        else:
            display_msg = msg

        if kwargs:
            extra.setdefault("custom_dimensions", {}).update(kwargs)

        self.logger.critical(
            display_msg if extra_data else msg, extra=extra if extra else None
        )

    def get_current_level(self):
        """현재 로그 레벨 반환"""
        return logging.getLevelName(self.logger.level)

    def is_debug_enabled(self):
        """디버그 모드 확인"""
        return self.logger.isEnabledFor(logging.DEBUG)

    def _setup_application_insights(self):
        """Application Insights 핸들러 설정"""
        try:
            # 환경변수에서 Application Insights Connection String 가져오기
            connection_string = os.getenv("agent-application-insights-connection-string")

            if not connection_string:
                # Connection String이 없으면 Instrumentation Key로 시도
                instrumentation_key = os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY")
                if instrumentation_key:
                    connection_string = f"InstrumentationKey={instrumentation_key}"

            if connection_string:
                from opencensus.ext.azure.log_exporter import AzureLogHandler
                import threading

                # Application Insights 핸들러 생성
                self.appinsights_handler = AzureLogHandler(
                    connection_string=connection_string
                )

                # AzureLogHandler의 lock이 None인 경우 수동으로 설정
                if not hasattr(self.appinsights_handler, 'lock') or self.appinsights_handler.lock is None:
                    self.appinsights_handler.lock = threading.RLock()

                # Application Insights 로그 레벨 설정
                appinsights_level = os.getenv("APPINSIGHTS_LOG_LEVEL", "INFO").upper()
                self.appinsights_handler.setLevel(
                    getattr(logging, appinsights_level, logging.INFO)
                )

                # 포맷터 설정 (Application Insights는 구조화된 로그를 선호)
                appinsights_formatter = logging.Formatter(
                    "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s",
                    "%Y-%m-%d %H:%M:%S",
                )
                self.appinsights_handler.setFormatter(appinsights_formatter)

                # 핸들러를 로거에 추가
                self.logger.addHandler(self.appinsights_handler)

                # Application Insights 활성화 로그는 나중에 출력 (초기화 완료 후)
                print("[INFO] Application Insights logging enabled")

            else:
                # Connection String이 없으면 콘솔에 출력 (로거 사용 X)
                if os.getenv("APP_ENV") in ["prod", "dev", "staging"]:
                    print(
                        "[WARNING] Application Insights connection string not found. "
                        "Set agent-application-insights-connection-string or APPINSIGHTS_INSTRUMENTATIONKEY environment variable."
                    )

        except ImportError:
            # 초기화 중에는 print 사용
            print(
                "[WARNING] opencensus-ext-azure not installed. Run: uv add opencensus-ext-azure"
            )
        except Exception as e:
            # 초기화 중 에러는 print로 출력
            import traceback
            print(f"[ERROR] Failed to setup Application Insights: {e}")
            traceback.print_exc()

    def set_appinsights_level(self, level: str):
        """Application Insights 출력 레벨만 변경"""
        if self.appinsights_handler:
            appinsights_level = getattr(logging, level.upper(), logging.INFO)
            self.appinsights_handler.setLevel(appinsights_level)
