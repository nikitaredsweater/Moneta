"""
This package contains the repositories for the application.
"""

# TODO: Make a base model that implements a selection of repository methods
# That should be present on all of the repositories

from app.repositories.user import User, UserRepository

__all__ = ['UserRepository', 'User']
