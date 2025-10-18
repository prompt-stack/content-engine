#!/usr/bin/env python3.11
"""Create OWNER user account for content engine."""

import asyncio
import sys
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User, UserRole, UserTier
from app.core.config import settings
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_owner_user():
    """Create an OWNER user account."""

    print("=" * 60)
    print("CREATE OWNER USER ACCOUNT")
    print("=" * 60)

    # Get user input
    email = input("\nEnter your email: ").strip()
    if not email:
        print("❌ Email cannot be empty")
        return

    password = getpass("Enter password: ").strip()
    if not password:
        print("❌ Password cannot be empty")
        return

    password_confirm = getpass("Confirm password: ").strip()
    if password != password_confirm:
        print("❌ Passwords do not match")
        return

    # Hash password
    hashed_password = pwd_context.hash(password)

    # Create database session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"\n⚠️  User with email {email} already exists!")
            update = input("Update to OWNER role? (y/N): ").strip().lower()

            if update == 'y':
                existing_user.role = UserRole.OWNER
                existing_user.tier = UserTier.OWNER
                existing_user.is_superuser = True
                existing_user.is_verified = True
                existing_user.is_active = True

                await session.commit()
                await session.refresh(existing_user)

                print("\n" + "=" * 60)
                print("✅ USER UPDATED TO OWNER")
                print("=" * 60)
                print(f"ID:     {existing_user.id}")
                print(f"Email:  {existing_user.email}")
                print(f"Role:   {existing_user.role.value}")
                print(f"Tier:   {existing_user.tier.value}")
                print("=" * 60)

                return existing_user.id
            else:
                print("❌ Cancelled")
                return None

        # Create new user
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=UserRole.OWNER,
            tier=UserTier.OWNER,
            is_active=True,
            is_superuser=True,
            is_verified=True,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        print("\n" + "=" * 60)
        print("✅ OWNER USER CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"ID:     {user.id}")
        print(f"Email:  {user.email}")
        print(f"Role:   {user.role.value}")
        print(f"Tier:   {user.tier.value}")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Authenticate with this email/password")
        print("2. Set up Google OAuth with this account")
        print("3. All extractions will be tied to this user")
        print("=" * 60)

        return user.id


if __name__ == "__main__":
    try:
        user_id = asyncio.run(create_owner_user())
        if user_id:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
