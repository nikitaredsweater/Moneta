"""
Environment variables and defaults.
"""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Environment variables and defaults.

    This is a singleton class that can be imported anywhere in the app.
    """

    # Database
    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_USER: str = 'postgres'
    DB_PASSWORD: str = 'postgres'
    DB_NAME: str = 'moneta_financial'
    DB_URL: str = (
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )

    # API
    API_VERSION: str = '0.0.1'
    API_HOST: str = '0.0.0.0'
    API_PORT: int = 8000

    # Logging
    LOG_LEVEL: str = 'INFO'
    LOG_FILE: str = 'app.log'
    LOG_MAX_BYTES: int = 1024 * 1024 * 5  # 5MB
    LOG_BACKUP_COUNT: int = 5


conf = Settings()
