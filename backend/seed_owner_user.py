#!/usr/bin/env python3.11
"""Seed OWNER user for testing and development."""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User, UserRole, UserTier
from app.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_owner_user():
    """Create OWNER user with default credentials."""

    # Default OWNER credentials
    email = "owner@contentengine.local"
    password = "owner123"  # Change this in production!

    print("=" * 60)
    print("SEEDING OWNER USER")
    print("=" * 60)
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Role: OWNER")
    print(f"Tier: OWNER")
    print("=" * 60)

    # Hash password
    hashed_password = pwd_context.hash(password)

    # Convert postgresql:// to postgresql+asyncpg:// for async support
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Create database session
    engine = create_async_engine(database_url, echo=False)
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
            print(f"\n⚠️  OWNER user already exists (ID: {existing_user.id})")
            print(f"   Email: {existing_user.email}")
            print(f"   Role: {existing_user.role.value}")
            print(f"   Tier: {existing_user.tier.value}")
            return existing_user.id

        # Create new OWNER user
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

        print(f"\n✅ OWNER USER CREATED")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role.value}")
        print(f"   Tier: {user.tier.value}")
        print("=" * 60)

        return user.id


if __name__ == "__main__":
    try:
        user_id = asyncio.run(seed_owner_user())
        print(f"\n✅ Success! User ID: {user_id}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
