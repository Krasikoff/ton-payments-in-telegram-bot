"""Здесь настройки приложения."""

from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR.parent / 'data/upload'
STATIC_DIR = BASE_DIR.parent / 'data/static'


class Settings(BaseSettings):
    """Содержит основные настройки приложения."""

    telegram_bot_token: str = '0000000000:El55gRI4rikAAHUdelfhmd......'
    mainnet_api_token: str = 'MAINNET_API_TOKEN'
    testnet_api_token: str = 'TESTNET_API_TOKEN'
    mainnet_wallet: str = 'MAINNET_WALLET'
    testnet_wallet:str = 'TESTNET_WALLET'
    work_mode: str = 'TEST_MODE'


    class Config:
        """Имя файла содержащего сами настройки."""

        env_file = '.env'


settings = Settings()
