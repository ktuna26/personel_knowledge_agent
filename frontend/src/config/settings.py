# src/config/settings.py
"""
Settings

Centralized config loader for Streamlit UI.
Supports .ini.
"""

import configparser
from os import path
from typing import Optional

from pydantic_settings import BaseSettings  # Pydantic import

from src.utils.logger import get_logger  # Local import

# Logger
logger = get_logger(__name__)
# Config path const
CONFIG_PATH = "src/config/cfg.ini"


class Settings(BaseSettings):
    """All application settings loaded from config file."""

    # Logging Configs
    # log_dir_name: Optional[str] = "logs"
    log_file_name: Optional[str] = "streamlit_app"
    log_level: Optional[str] = "INFO"

    # Agent Configs
    agent_name: Optional[str] = None
    agent_api: Optional[tuple] = None
    request_timeout: Optional[int] = 60

    # Streamlit Configs
    st_layout: Optional[str] = None
    page_icon: Optional[str] = None
    avatar_user: Optional[str] = None
    avatar_assistant: Optional[str] = None
    session_key: Optional[str] = None

    # CMD Configs
    console_handler: Optional[bool] = None

    # Optional Configs
    # ENABLE_WELL_LOG_REPORT: bool = False

    class Config:
        extra = "allow"
        case_sensitive = False
        populate_by_name = True


class SettingsLoader:
    """
    Loads settings from a .ini config file and optionally from environment.
    """

    def __init__(self, config_path: str):
        """
        Initialize SettingsLoader with a path to a configuration file.

        Args:
            config_path (str): Path to the .ini config file.
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_ini()

    def _load_ini(self) -> None:
        """Loads the config.ini file into memory."""
        if not path.exists(self.config_path):
            logger.critical(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, encoding="utf-8") as f:
            self.config.read_file(f)

    def _parse_string(self, setting_name) -> Optional[str]:
        """
        Retrieves a setting from the configuration file.

        Args:
            setting_name (str): The name of the prompt to retrieve.

        Returns:
            Optional[str]:: The setting, else None.
        """
        return self.config.get("Settings", setting_name)

    def _parse_bool(self, setting_name) -> Optional[bool]:
        """
        Retrieves a setting from the configuration file.

        Args:
            setting_name (str): The name of the prompt to retrieve.

        Returns:
            Optional[str]:: The setting, else None.
        """
        return self.config.getboolean("Settings", setting_name)

    def _parse_int(self, setting_name) -> Optional[int]:
        """
        Retrieves a setting from the configuration file.

        Args:
            setting_name (str): The name of the prompt to retrieve.

        Returns:
            Optional[str]:: The setting, else None.
        """
        return self.config.getint("Settings", setting_name)

    def _parse_float(self, setting_name) -> Optional[float]:
        """
        Retrieves a setting from the configuration file.

        Args:
            setting_name (str): The name of the prompt to retrieve.

        Returns:
            Optional[str]:: The setting, else None.
        """
        return self.config.getfloat("Settings", setting_name)

    def _parse_list_or_tuple(
            self,
            key: str,
            data_type: type = str,
            collection_type: type = tuple,
            default=None,
            delimiter: str = ","
        ):
        """
        Parse a config value as a typed list or tuple using the appropriate _parse_* method.

        Args:
            key (str): Config key name (e.g., 'MY_ENV_VAR')
            data_type (type): Type of elements (e.g., int, float, bool). Defaults to str.
            collection_type (type): `list` or `tuple`. Defaults to list.
            default (list or tuple, optional): Default if missing or invalid. Defaults to empty collection.
            delimiter (str): Delimiter for splitting. Defaults to ','.

        Returns:
            list or tuple: Parsed list or tuple of typed values.
        """
        default = default if default is not None else collection_type()
        
        # Dynamically select the right primitive parser
        parser_dispatch = {
            str: self._parse_string,
            int: self._parse_int,
            float: self._parse_float,
            bool: self._parse_bool
        }
        base_parser = parser_dispatch[data_type]

        # Get the raw string value from config using the correct _parse_* method
        raw = base_parser(key)
        if not raw:
            return default

        try:
            # Parse each item to the desired type
            parsed = [type_fn(item.strip()) for item in str(raw).split(delimiter) if item.strip()]
            return collection_type(parsed)
        except Exception:
            return default

    def build_settings(self) -> Settings:
        """
        Builds and returns a populated Settings object.

        Returns:
            Settings: Fully populated application settings object.

        Raises:
            ValueError: If required paths or environment config is missing.
        """
        s = Settings(
            # log_dir_name=self._parse_string("log_dir_name"),
            log_file_name=self._parse_string("log_file_name"),
            log_level=self._parse_string("log_level"),
            agent_name=self._parse_string("agent_name"),
            agent_api=self._parse_list_or_tuple("agent_api"),
            request_timeout=self._parse_int("request_timeout"),
            st_layout=self._parse_string("streamlit_layout"),
            page_icon=self._parse_string("page_icon"),
            avatar_user=self._parse_string("avatar_user"),
            avatar_assistant=self._parse_string("avatar_assistant"),
            session_key=self._parse_string("session_key"),
            console_handler=self._parse_string("console_handler"),
        )
        logger.info("Application settings loaded successfully.")
        return s


# Global settings
settings_loader = SettingsLoader(CONFIG_PATH)
settings = settings_loader.build_settings()

# Validate essential settings
required_settings = [
    "log_file_name",
    "log_level",
    "agent_name",
    "agent_api",
    "request_timeout",
    "st_layout",
    "page_icon",
    "avatar_user",
    "avatar_assistant",
    "session_key",
    "console_handler",
]

missing_settings = [k for k in required_settings if getattr(settings, k, None) is None]
if missing_settings:
    logger.critical(f"Missing required config keys: {missing_settings}")
    raise SystemExit(f"Missing required config keys: {missing_settings}")
