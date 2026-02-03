"""
User data configuration.
"""
from database.models import UserData
from .settings import settings


def get_user_data() -> UserData:
    """Get user data from settings."""
    return UserData(
        student_name=settings.student_name,
        student_id=settings.student_id
    )
