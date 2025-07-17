# src/config/settings.py
"""
Settings

Centralized config loader for Personel Knowledge Agent.
Supports .env, and .ini.
"""

import configparser
from enum import Enum
from os import getenv, path
from typing import Any, Dict, List, Optional

# Pydantic imports
from pydantic import Field
from pydantic_settings import BaseSettings

# Local imports
from src.utils.logger import get_logger

# Logger
logger = get_logger(__name__)
# Config path const
CONFIG_PATH = "src/config/cfg.ini"


class Settings(BaseSettings):
    """All application settings loaded from .env, .ini, or Key Vault."""
    # Env Settings
    # 

    # Model / API Keys
    openai_api_key: Optional[str] = Field(default=None, alias="openai-api-key")
    openai_api_url: Optional[str] = Field(default=None, alias="openai-api-url")
    openai_model_name: Optional[str] = Field(default=None, alias="openai-model-name")

    # Logging Configs
    # log_dir_name: Optional[str] = "logs"
    log_file_name: Optional[str] = "sk_sdk_app"
    log_level: Optional[str] = "INFO"

    # Agent Configs
    retry_timeout: Optional[float] = None
    agent_description: Optional[str] = None
    agent_endpoint: Optional[str] = None
    endpoint_healthcheck: Optional[bool] = None

    # Prompt Configs
    prompt_base_path: Optional[str] = None
    system_prompt_name: Optional[str] = None

    # CMD Configs
    console_handler: Optional[bool] = None
    cmd_exit: Optional[str] = None
    cmd_history: Optional[str] = None

    # Reporting Configs
    report_base_path: Optional[str] = None
    report_name: Optional[str] = None

    class Config:
        extra = "allow"
        env_file = None
        case_sensitive = False
        populate_by_name = True


class SettingsLoader:
    """
    Loads settings from .ini, then .env, then optionally Azure Key Vault.
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
        """Load the INI config file into memory."""
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
        Build and return a populated Settings object.

        Returns:
            Settings: Populated settings object.
        Raises:
            ValueError: If required configuration is missing.
        """
        env_path = self._parse_string("env_path")
        if not env_path:
            raise ValueError("Missing 'env_path' in INI configuration.")

        s = Settings(
            _env_file=env_path,
            log_file_name=self._parse_string("log_file_name"),
            log_level=self._parse_string("log_level"),
            retry_timeout=self._parse_float("retry_timeout"),
            agent_description=self._parse_string("agent_description"),
            agent_endpoint=self._parse_string("agent_endpoint"),
            endpoint_healthcheck=self._parse_bool("endpoint_healthcheck"),
            prompt_base_path=self._parse_string("prompt_base_path"),
            system_prompt_name=self._parse_string("system_prompt_name"),
            console_handler=self._parse_bool("console_handler"),
            cmd_exit=self._parse_string("cmd_exit"),
            cmd_history=self._parse_string("cmd_history"),
            report_base_path=self._parse_string("report_base_path"),
            report_name=self._parse_string("report_name"),
        )
        logger.info("Application settings loaded successfully.")
        return s


# Global settings
settings_loader = SettingsLoader(CONFIG_PATH)
settings = settings_loader.build_settings()

required_keys = [
    "openai_api_key",
    "openai_api_url",
    "openai_model_name",
    "log_file_name",
    "log_level",
    "retry_timeout",
    "agent_description",
    "agent_endpoint",
    "endpoint_healthcheck",
    "prompt_base_path",
    "system_prompt_name",
    "console_handler",
    "cmd_exit",
    "cmd_history",
    "report_base_path",
    "report_name",
]

missing_keys = [k for k in required_keys if getattr(settings, k, None) is None]
if missing_keys:
    logger.warning(f"Missing required config keys: {missing_keys}")
    # raise SystemExit(f"Missing required config keys: {missing_keys}")
