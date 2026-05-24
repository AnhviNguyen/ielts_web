"""
app/repositories/user_repository.py
─────────────────────────────────────
Database operations for the User model only.
No business logic — pure CRUD.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: int) -> User | None:
        """Fetch a user by primary key."""
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address (case-sensitive)."""
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, email: str, password_hash: str, role: str = "user") -> User:
        """Insert a new user row and return the persisted object."""
        user = User(email=email, password_hash=password_hash, role=role)
        self._db.add(user)
        await self._db.flush()   # get auto-assigned id without committing
        await self._db.refresh(user)
        return user
