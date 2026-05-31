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
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self._db.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        password_hash: str,
        role: str = "user",
        google_id: str | None = None,
        is_verified: bool = False,
        auth_provider: str = "email",
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
            google_id=google_id,
            is_verified=is_verified,
            auth_provider=auth_provider,
        )
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def mark_verified(self, user: User) -> User:
        user.is_verified = True
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def update_google_id(self, user: User, google_id: str) -> User:
        user.google_id = google_id
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def update_password_hash(self, user: User, password_hash: str) -> User:
        user.password_hash = password_hash
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user
