"""Configuration module for the application."""

import os


class Config:
    """Application configuration."""

    def __init__(self) -> None:
        self.connection_string = self._get_database_url()
        self.asyncpg_connection_string = self._get_async_database_url()
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))

    def _get_database_url(self) -> str:
        """
        Get database URL from environment variables
        for synchronous connections.

        Returns:
            str: The database URL for synchronous connections.
        """

        # TODO: Add a support for the DATABASE_URL to be used from
        # the environment variables.

        # Try to get from environment first
        database_url = os.getenv('DATABASE_URL')

        if database_url:
            # Replace psycopg2 with psycopg if present in the URL
            if (
                'postgresql://' in database_url
                and 'psycopg2' not in database_url
            ):
                return database_url.replace(
                    'postgresql://', 'postgresql+psycopg://'
                )
            return database_url

        # Fallback to default development database with psycopg driver
        return 'postgresql+psycopg://postgres:postgres@localhost:5432/moneta'

    def _get_async_database_url(self) -> str:
        """
        Get async database URL from environment variables.

        Returns:
            str: The database URL for asynchronous connections.
        """

        # TODO: Add a support for the DATABASE_URL to be used from
        # the environment variables.

        # Try to get from environment first
        database_url = os.getenv('DATABASE_URL')

        if database_url:
            # Convert to async format
            if 'postgresql://' in database_url:
                return database_url.replace(
                    'postgresql://', 'postgresql+asyncpg://'
                )
            if 'postgresql+psycopg://' in database_url:
                return database_url.replace(
                    'postgresql+psycopg://', 'postgresql+asyncpg://'
                )
            return database_url

        # Fallback to default development database with asyncpg driver
        return 'postgresql+asyncpg://postgres:postgres@localhost:5432/moneta'


# Global configuration instance
conf = Config()
