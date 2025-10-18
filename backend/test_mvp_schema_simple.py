#!/usr/bin/env python3.11
"""
Simple MVP Schema Tests (No pytest - pure async/await)

Tests:
1. Full hierarchy: users → extractions → email_content → extracted_links
2. CASCADE delete behavior
3. Config persistence
"""

import asyncio
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User, UserRole, UserTier
from app.models.newsletter_extraction import Extraction, EmailContent, ExtractedLink, NewsletterConfig
from app.core.config import settings
from app.crud import newsletter_extraction as crud


async def test_full_hierarchy():
    """Test 1: Create complete data hierarchy."""
    print("\n" + "=" * 60)
    print("TEST 1: Full Hierarchy (users → extractions → content → links)")
    print("=" * 60)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get OWNER user
        result = await db.execute(select(User).where(User.email == "owner@contentengine.local"))
        user = result.scalar_one()
        print(f"✅ Found OWNER user: id={user.id}, email={user.email}")

        # Create extraction
        extraction_id = f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        extraction = Extraction(
            id=extraction_id,
            user_id=user.id,  # ← Tied to user
            created_at=datetime.utcnow(),
            days_back=7,
            max_results=30,
        )
        db.add(extraction)
        await db.flush()
        print(f"✅ Created extraction: {extraction_id} for user_id={user.id}")

        # Create email content
        email_content = EmailContent(
            extraction_id=extraction_id,
            subject="Test Newsletter",
            sender="test@newsletter.com",
            date="2025-10-16 12:00:00",
        )
        db.add(email_content)
        await db.flush()
        print(f"✅ Created email_content: id={email_content.id}")

        # Create extracted links
        link1 = ExtractedLink(
            content_id=email_content.id,
            url="https://example.com/article1",
            original_url="https://tracking.com/link1",
        )
        link2 = ExtractedLink(
            content_id=email_content.id,
            url="https://example.com/article2",
        )
        db.add_all([link1, link2])
        await db.commit()
        print(f"✅ Created 2 extracted_links")

        # Verify hierarchy by reloading
        result = await db.execute(
            select(Extraction).where(Extraction.id == extraction_id)
        )
        saved_extraction = result.unique().scalar_one()

        assert saved_extraction.user_id == user.id, "❌ user_id mismatch!"
        assert len(saved_extraction.content_items) == 1, "❌ Should have 1 email_content!"
        assert len(saved_extraction.content_items[0].links) == 2, "❌ Should have 2 links!"

        print(f"✅ VERIFIED: user({user.id}) → extraction → content → 2 links")
        print("=" * 60)

        # Cleanup
        await db.execute(delete(Extraction).where(Extraction.id == extraction_id))
        await db.commit()

    return True


async def test_cascade_delete():
    """Test 2: CASCADE delete behavior."""
    print("\n" + "=" * 60)
    print("TEST 2: CASCADE Delete Behavior")
    print("=" * 60)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get OWNER user
        result = await db.execute(select(User).where(User.email == "owner@contentengine.local"))
        user = result.scalar_one()

        # Create test data
        extraction_id = f"cascade_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        extraction = Extraction(
            id=extraction_id,
            user_id=user.id,
            created_at=datetime.utcnow(),
        )
        db.add(extraction)
        await db.flush()

        email_content = EmailContent(
            extraction_id=extraction_id,
            subject="Cascade Test",
            sender="test@cascade.com",
            date="2025-10-16",
        )
        db.add(email_content)
        await db.flush()

        content_id = email_content.id

        link = ExtractedLink(
            content_id=email_content.id,
            url="https://cascade.test/link",
        )
        db.add(link)
        await db.commit()

        print(f"✅ Created: extraction → content → link")

        # Delete extraction (should CASCADE to content and links)
        await db.execute(delete(Extraction).where(Extraction.id == extraction_id))
        await db.commit()
        print(f"✅ Deleted extraction: {extraction_id}")

        # Verify CASCADE delete
        result_content = await db.execute(
            select(EmailContent).where(EmailContent.id == content_id)
        )
        content_after = result_content.scalar_one_or_none()

        result_links = await db.execute(
            select(ExtractedLink).where(ExtractedLink.content_id == content_id)
        )
        links_after = result_links.scalars().all()

        assert content_after is None, "❌ EmailContent should be deleted (CASCADE)!"
        assert len(links_after) == 0, "❌ ExtractedLinks should be deleted (CASCADE)!"

        print(f"✅ VERIFIED: CASCADE deleted content and links")
        print("=" * 60)

    return True


async def test_config_persistence():
    """Test 3: Config persistence."""
    print("\n" + "=" * 60)
    print("TEST 3: Config Persistence")
    print("=" * 60)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get OWNER user
        result = await db.execute(select(User).where(User.email == "owner@contentengine.local"))
        user = result.scalar_one()

        # Test upsert (create or update)
        config_data = {
            "newsletters": {"enabled": True},
            "content_filtering": {
                "whitelist_domains": ["github.com", "test.com"],
                "blacklist_domains": ["spam.com"],
            },
        }

        created_config = await crud.upsert_config(db, config_data, user.id)
        print(f"✅ Upserted config for user_id={user.id}")

        # Test get
        retrieved_config = await crud.get_config(db, user.id)

        assert retrieved_config is not None, "❌ Config should exist!"
        assert "github.com" in retrieved_config["content_filtering"]["whitelist_domains"], "❌ Whitelist mismatch!"

        print(f"✅ Retrieved config successfully")

        # Test update (upsert again)
        config_data["content_filtering"]["whitelist_domains"].append("arxiv.org")
        updated_config = await crud.upsert_config(db, config_data, user.id)
        print(f"✅ Updated config (added arxiv.org)")

        # Verify update
        final_config = await crud.get_config(db, user.id)

        assert "arxiv.org" in final_config["content_filtering"]["whitelist_domains"], "❌ Update failed!"

        print(f"✅ VERIFIED: Config persists and updates correctly")
        print("=" * 60)

    return True


async def test_existing_data():
    """Test 4: Verify existing extractions are tied to OWNER."""
    print("\n" + "=" * 60)
    print("TEST 4: Verify Existing Extractions")
    print("=" * 60)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get OWNER user
        result = await db.execute(select(User).where(User.email == "owner@contentengine.local"))
        user = result.scalar_one()

        # Get all extractions
        result = await db.execute(
            select(Extraction).where(Extraction.user_id == user.id)
        )
        extractions = result.unique().scalars().all()

        print(f"✅ Found {len(extractions)} extractions for OWNER (user_id={user.id})")

        for extraction in extractions:
            print(f"   - {extraction.id} (created: {extraction.created_at})")

        # Verify at least some exist
        assert len(extractions) > 0, "❌ Should have at least 1 extraction!"

        print(f"✅ VERIFIED: Existing extractions are tied to OWNER")
        print("=" * 60)

    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print(" " * 20 + "CONTENT ENGINE MVP SCHEMA TESTS")
    print("=" * 80)

    try:
        # Run tests
        test1 = await test_full_hierarchy()
        test2 = await test_cascade_delete()
        test3 = await test_config_persistence()
        test4 = await test_existing_data()

        # Summary
        print("\n" + "=" * 80)
        print(" " * 30 + "TEST SUMMARY")
        print("=" * 80)
        print(f"✅ TEST 1: Full Hierarchy - PASSED")
        print(f"✅ TEST 2: CASCADE Delete - PASSED")
        print(f"✅ TEST 3: Config Persistence - PASSED")
        print(f"✅ TEST 4: Existing Data - PASSED")
        print("=" * 80)
        print(" " * 25 + "🎉 ALL TESTS PASSED! 🎉")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
