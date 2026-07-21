import asyncio
import getpass

from sqlalchemy import or_, select

from app.core.security import hash_password
from app.db.session import AsyncSessionFactory, close_database
from app.models.core import GlobalRole, User, UserRole, UserStatus


async def create_superadmin() -> None:
    email = input("Email: ").strip().lower()
    login = input("Login: ").strip().lower()
    display_name = input("Display name: ").strip() or None
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Repeat password: ")

    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(User).where(
                or_(User.email == email, User.login == login)
            )
        )
        if result.scalar_one_or_none() is not None:
            raise SystemExit("User with this email or login already exists.")

        user = User(
            email=email,
            login=login,
            display_name=display_name,
            password_hash=hash_password(password),
            status=UserStatus.ACTIVE,
            email_verified=True,
        )
        session.add(user)
        await session.flush()

        session.add(
            UserRole(
                user_id=user.id,
                role=GlobalRole.SUPERADMIN,
            )
        )

        await session.commit()
        print(f"Superadmin created: {login} ({email})")


async def main() -> None:
    try:
        await create_superadmin()
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
