"""One-off CLI: reset password for a user by email. Usage: python reset_user_password.py email new_password"""
import asyncio
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import AsyncSessionLocal
from app.db.models import User


async def main(email: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"NOT_FOUND: {email}")
            sys.exit(1)
        user.password_hash = hash_password(password)
        user.is_verified = True
        user.is_active = True
        await db.commit()
        print(f"OK role={user.role} email={user.email}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_user_password.py <email> <new_password>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
