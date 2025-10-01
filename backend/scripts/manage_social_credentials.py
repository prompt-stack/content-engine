#!/usr/bin/env python3
"""
Manage Social Media Credentials
Set up and manage OAuth credentials for social media platforms

Usage:
    python scripts/manage_social_credentials.py
"""

import asyncio
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.user import User


class SocialCredentialManager:
    """Manage social media OAuth credentials"""

    PLATFORMS = {
        "twitter": {
            "name": "Twitter (X)",
            "fields": ["api_key", "api_secret", "access_token", "access_secret"],
            "connected_field": "twitter_connected"
        },
        "linkedin": {
            "name": "LinkedIn",
            "fields": ["client_id", "client_secret", "access_token"],
            "connected_field": "linkedin_connected"
        },
        "reddit": {
            "name": "Reddit",
            "fields": ["client_id", "client_secret", "username", "password"],
            "connected_field": "reddit_connected"
        },
        "youtube": {
            "name": "YouTube",
            "fields": ["client_id", "client_secret"],
            "connected_field": "youtube_connected"
        },
        "facebook": {
            "name": "Facebook",
            "fields": ["app_id", "app_secret", "page_access_token", "page_id"],
            "connected_field": "facebook_connected"
        },
        "instagram": {
            "name": "Instagram",
            "fields": ["app_id", "app_secret", "account_id", "page_token"],
            "connected_field": "instagram_connected"
        }
    }

    def __init__(self):
        self.credentials_dir = Path("config/social_credentials")
        self.credentials_dir.mkdir(parents=True, exist_ok=True)

    def _get_credential_path(self, user_id: int, platform: str) -> Path:
        """Get path to credential file for user and platform"""
        return self.credentials_dir / f"user_{user_id}_{platform}.json"

    def save_credentials(self, user_id: int, platform: str, credentials: dict):
        """Save credentials to file"""
        path = self._get_credential_path(user_id, platform)
        with open(path, 'w') as f:
            json.dump(credentials, f, indent=2)
        print(f"✅ Credentials saved to {path}")

    def load_credentials(self, user_id: int, platform: str) -> dict:
        """Load credentials from file"""
        path = self._get_credential_path(user_id, platform)
        if not path.exists():
            return {}

        with open(path, 'r') as f:
            return json.load(f)

    def list_connected_platforms(self, user_id: int) -> list:
        """List all connected platforms for user"""
        connected = []
        for platform in self.PLATFORMS.keys():
            path = self._get_credential_path(user_id, platform)
            if path.exists():
                connected.append(platform)
        return connected

    async def setup_platform(self, user_id: int, platform: str):
        """Interactive setup for a platform"""
        if platform not in self.PLATFORMS:
            print(f"❌ Unknown platform: {platform}")
            return

        info = self.PLATFORMS[platform]
        print()
        print(f"🔐 Setting up {info['name']}")
        print("=" * 60)
        print()

        credentials = {}
        for field in info["fields"]:
            value = input(f"{field.replace('_', ' ').title()}: ").strip()
            if value:
                credentials[field] = value

        if credentials:
            self.save_credentials(user_id, platform, credentials)

            # Update user's connected status
            engine = create_async_engine(settings.DATABASE_URL, echo=False)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

            async with async_session() as session:
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()

                if user:
                    setattr(user, info["connected_field"], True)
                    await session.commit()
                    print(f"✅ {info['name']} connected for user {user.email}")

            await engine.dispose()
        else:
            print("❌ No credentials provided")


async def main():
    """Main menu"""
    print()
    print("=" * 60)
    print("🔐 Social Media Credential Manager")
    print("=" * 60)
    print()

    # Get user email
    email = input("Enter user email (or press Enter for owner@contentengine.ai): ").strip()
    if not email:
        email = "owner@contentengine.ai"

    # Load user
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ User not found: {email}")
            await engine.dispose()
            return

        print(f"✅ Found user: {user.email} (ID: {user.id}, Role: {user.role.value})")
        print()

    await engine.dispose()

    manager = SocialCredentialManager()

    # Show connected platforms
    connected = manager.list_connected_platforms(user.id)
    print("Connected Platforms:")
    if connected:
        for platform in connected:
            print(f"  ✅ {manager.PLATFORMS[platform]['name']}")
    else:
        print("  (none)")
    print()

    # Main menu
    while True:
        print("=" * 60)
        print("Options:")
        print("  1. Connect Twitter (X)")
        print("  2. Connect LinkedIn")
        print("  3. Connect Reddit")
        print("  4. Connect YouTube")
        print("  5. Connect Facebook")
        print("  6. Connect Instagram")
        print("  7. View all credentials")
        print("  0. Exit")
        print()

        choice = input("Choose option: ").strip()

        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            await manager.setup_platform(user.id, "twitter")
        elif choice == "2":
            await manager.setup_platform(user.id, "linkedin")
        elif choice == "3":
            await manager.setup_platform(user.id, "reddit")
        elif choice == "4":
            await manager.setup_platform(user.id, "youtube")
        elif choice == "5":
            await manager.setup_platform(user.id, "facebook")
        elif choice == "6":
            await manager.setup_platform(user.id, "instagram")
        elif choice == "7":
            print()
            print("Connected Platforms:")
            for platform in manager.PLATFORMS.keys():
                creds = manager.load_credentials(user.id, platform)
                if creds:
                    print(f"\n{manager.PLATFORMS[platform]['name']}:")
                    for key, value in creds.items():
                        # Mask sensitive values
                        if "secret" in key.lower() or "password" in key.lower() or "token" in key.lower():
                            display_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
                        else:
                            display_value = value
                        print(f"  {key}: {display_value}")
            print()
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())