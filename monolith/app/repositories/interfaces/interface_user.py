"""
Interface for the UserRepository
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.schemas import User, UserCreate


class IUserRepository(ABC):

    @abstractmethod
    async def add_user(self, user_data: UserCreate) -> bool:
        """
        Create user using the DTO for the UserCreate (schemas)

        Args:
            user_data (UserCreate) - UserCreate DTO

        Returns:
            bool - True if the user was added successfully, False otherwise
        """
        pass

    @abstractmethod
    async def get_all_users(self) -> Optional[List[User]]:
        """
        Returns all users from the database, if any

        Returns:
            Optional[List[User]] - List of users or null
        """
        pass
