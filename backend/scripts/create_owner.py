#!/usr/bin/env python3
"""
Create Owner Account
Creates the system owner account with unlimited access

Usage:
    python scripts/create_owner.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User, UserRole, UserTier
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_owner_account():
    """Create the system owner account"""

    print("=" * 60)
    print("🔐 Content Engine - Create Owner Account")
    print("=" * 60)
    print()

    # Get owner details
    print("Enter owner account details:")
    email = input("Email: ").strip()

    if not email:
        print("❌ Email is required")
        return

    # Get password
    import getpass
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm Password: ")

    if password != password_confirm:
        print("❌ Passwords don't match")
        return

    if len(password) < 8:
        print("❌ Password must be at least 8 characters")
        return

    print()
    print("Creating owner account...")

    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if user already exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"⚠️  User with email {email} already exists")

            # Ask to upgrade to owner
            upgrade = input("Upgrade existing user to OWNER? (yes/no): ").strip().lower()
            if upgrade == "yes":
                existing_user.role = UserRole.OWNER
                existing_user.tier = UserTier.OWNER
                existing_user.is_superuser = True
                existing_user.is_verified = True
                existing_user.is_active = True

                await session.commit()
                print(f"✅ User {email} upgraded to OWNER")
            else:
                print("❌ Cancelled")
            return

        # Create new owner user
        hashed_password = pwd_context.hash(password)

        owner = User(
            email=email,
            hashed_password=hashed_password,
            role=UserRole.OWNER,
            tier=UserTier.OWNER,
            is_superuser=True,
            is_verified=True,
            is_active=True
        )

        session.add(owner)
        await session.commit()
        await session.refresh(owner)

        print()
        print("=" * 60)
        print("✅ OWNER ACCOUNT CREATED SUCCESSFULLY")
        print("=" * 60)
        print()
        print(f"📧 Email: {owner.email}")
        print(f"👤 User ID: {owner.id}")
        print(f"🎭 Role: {owner.role.value}")
        print(f"🎫 Tier: {owner.tier.value}")
        print(f"📊 Rate Limit: UNLIMITED")
        print()
        print("Privileges:")
        print(f"  ✅ is_owner: {owner.is_owner}")
        print(f"  ✅ is_superuser: {owner.is_superuser}")
        print(f"  ✅ is_admin: {owner.is_admin}")
        print(f"  ✅ can_manage_users: {owner.can_manage_users}")
        print(f"  ✅ can_manage_system: {owner.can_manage_system}")
        print(f"  ✅ can_bypass_limits: {owner.can_bypass_limits}")
        print()
        print("🔑 You can now login with these credentials")
        print()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_owner_account())