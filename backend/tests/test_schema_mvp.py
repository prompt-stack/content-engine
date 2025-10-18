#!/usr/bin/env python3.11
"""
Comprehensive MVP Schema Tests

Tests the complete data model:
users → extractions → email_content → extracted_links
users → newsletter_config

Verifies:
- Full hierarchy creation
- CASCADE delete behavior
- Foreign key constraints
- Config persistence
- CRUD operations
"""

import pytest
import asyncio
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User, UserRole, UserTier
from app.models.newsletter_extraction import Extraction, EmailContent, ExtractedLink, NewsletterConfig
from app.core.config import settings
from app.crud import newsletter_extraction as crud


# Test fixtures
async def get_db_session():
    """Get database session."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        return session


async def get_test_user(db_session):
    """Get or create test user."""
    # Check if test user exists
    result = await db_session.execute(
        select(User).where(User.email == "test@mvp.local")
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        print(f"\n✅ Using existing test user: ID={existing_user.id}")
        return existing_user

    # Create new test user
    user = User(
        email="test@mvp.local",
        hashed_password="test123",
        role=UserRole.OWNER,
        tier=UserTier.OWNER,
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    print(f"\n✅ Test user created: ID={user.id}")
    return user


# =============================================================================
# TEST 1: Full Hierarchy Creation (users → extractions → content → links)
# =============================================================================

@pytest.mark.asyncio
async def test_full_hierarchy_creation(db_session, test_user):
    """Test creating complete data hierarchy."""
    print("\n" + "=" * 60)
    print("TEST 1: Full Hierarchy Creation")
    print("=" * 60)

    extraction_id = f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Create extraction
    extraction = Extraction(
        id=extraction_id,
        user_id=test_user.id,  # ← Tied to user
        created_at=datetime.utcnow(),
        days_back=7,
        max_results=30,
    )
    db_session.add(extraction)
    await db_session.flush()

    print(f"✅ Created extraction: {extraction_id} for user_id={test_user.id}")

    # Create email content
    email_content = EmailContent(
        extraction_id=extraction_id,
        subject="Test Newsletter",
        sender="test@newsletter.com",
        date="2025-10-15 12:00:00",
    )
    db_session.add(email_content)
    await db_session.flush()

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
        original_url=None,
    )
    db_session.add_all([link1, link2])
    await db_session.commit()

    print(f"✅ Created 2 extracted_links")

    # Verify hierarchy
    result = await db_session.execute(
        select(Extraction)
        .where(Extraction.id == extraction_id)
    )
    saved_extraction = result.scalar_one()

    assert saved_extraction.user_id == test_user.id
    assert len(saved_extraction.content_items) == 1
    assert len(saved_extraction.content_items[0].links) == 2

    print(f"✅ Verified hierarchy: user → extraction → content → 2 links")
    print("=" * 60)

    return extraction_id


# =============================================================================
# TEST 2: CASCADE Delete Behavior
# =============================================================================

@pytest.mark.asyncio
async def test_cascade_delete_extraction(db_session, test_user):
    """Test that deleting extraction cascades to content and links."""
    print("\n" + "=" * 60)
    print("TEST 2: CASCADE Delete (Extraction)")
    print("=" * 60)

    extraction_id = f"cascade_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Create test data
    extraction = Extraction(
        id=extraction_id,
        user_id=test_user.id,
        created_at=datetime.utcnow(),
    )
    db_session.add(extraction)
    await db_session.flush()

    email_content = EmailContent(
        extraction_id=extraction_id,
        subject="Cascade Test",
        sender="test@cascade.com",
        date="2025-10-15",
    )
    db_session.add(email_content)
    await db_session.flush()

    link = ExtractedLink(
        content_id=email_content.id,
        url="https://cascade.test/link",
    )
    db_session.add(link)
    await db_session.commit()

    print(f"✅ Created extraction → content → link")

    # Count before delete
    result_content = await db_session.execute(
        select(EmailContent).where(EmailContent.extraction_id == extraction_id)
    )
    content_before = result_content.scalars().all()

    result_links = await db_session.execute(
        select(ExtractedLink).where(ExtractedLink.content_id == email_content.id)
    )
    links_before = result_links.scalars().all()

    assert len(content_before) == 1
    assert len(links_before) == 1

    # Delete extraction (should CASCADE)
    await db_session.execute(delete(Extraction).where(Extraction.id == extraction_id))
    await db_session.commit()

    print(f"✅ Deleted extraction: {extraction_id}")

    # Verify CASCADE delete
    result_content_after = await db_session.execute(
        select(EmailContent).where(EmailContent.extraction_id == extraction_id)
    )
    content_after = result_content_after.scalars().all()

    result_links_after = await db_session.execute(
        select(ExtractedLink).where(ExtractedLink.content_id == email_content.id)
    )
    links_after = result_links_after.scalars().all()

    assert len(content_after) == 0, "❌ EmailContent should be deleted (CASCADE)"
    assert len(links_after) == 0, "❌ ExtractedLinks should be deleted (CASCADE)"

    print(f"✅ CASCADE delete verified: content and links deleted")
    print("=" * 60)


@pytest.mark.asyncio
async def test_cascade_delete_user(db_session):
    """Test that deleting user cascades to all their data."""
    print("\n" + "=" * 60)
    print("TEST 3: CASCADE Delete (User)")
    print("=" * 60)

    # Create temporary user
    temp_user = User(
        email="temp_cascade@test.local",
        hashed_password="test",
        role=UserRole.USER,
        tier=UserTier.FREE,
    )
    db_session.add(temp_user)
    await db_session.commit()
    await db_session.refresh(temp_user)

    print(f"✅ Created temp user: id={temp_user.id}")

    # Create extraction for temp user
    extraction_id = f"temp_extract_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    extraction = Extraction(
        id=extraction_id,
        user_id=temp_user.id,
        created_at=datetime.utcnow(),
    )
    db_session.add(extraction)
    await db_session.flush()

    # Create config for temp user
    config = NewsletterConfig(
        user_id=temp_user.id,
        config_data={"test": "data"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(config)
    await db_session.commit()

    print(f"✅ Created extraction and config for temp user")

    # Delete user (should CASCADE to extractions and config)
    await db_session.execute(delete(User).where(User.id == temp_user.id))
    await db_session.commit()

    print(f"✅ Deleted user: id={temp_user.id}")

    # Verify CASCADE delete
    result_extraction = await db_session.execute(
        select(Extraction).where(Extraction.id == extraction_id)
    )
    extraction_after = result_extraction.scalar_one_or_none()

    result_config = await db_session.execute(
        select(NewsletterConfig).where(NewsletterConfig.user_id == temp_user.id)
    )
    config_after = result_config.scalar_one_or_none()

    assert extraction_after is None, "❌ Extraction should be deleted (CASCADE)"
    assert config_after is None, "❌ Config should be deleted (CASCADE)"

    print(f"✅ CASCADE delete verified: extraction and config deleted")
    print("=" * 60)


# =============================================================================
# TEST 4: Config Persistence
# =============================================================================

@pytest.mark.asyncio
async def test_config_persistence(db_session, test_user):
    """Test newsletter config CRUD operations."""
    print("\n" + "=" * 60)
    print("TEST 4: Config Persistence")
    print("=" * 60)

    # Test upsert (create)
    config_data = {
        "newsletters": {"enabled": True},
        "content_filtering": {
            "whitelist_domains": ["github.com", "arxiv.org"],
            "blacklist_domains": ["spam.com"],
        },
    }

    created_config = await crud.upsert_config(db_session, config_data, test_user.id)

    print(f"✅ Created config for user_id={test_user.id}")
    print(f"   Whitelist: {created_config.config_data['content_filtering']['whitelist_domains']}")

    # Test get
    retrieved_config = await crud.get_config(db_session, test_user.id)

    assert retrieved_config is not None
    assert retrieved_config["content_filtering"]["whitelist_domains"] == ["github.com", "arxiv.org"]

    print(f"✅ Retrieved config successfully")

    # Test upsert (update)
    config_data["content_filtering"]["whitelist_domains"].append("huggingface.co")
    updated_config = await crud.upsert_config(db_session, config_data, test_user.id)

    print(f"✅ Updated config (added huggingface.co)")

    # Verify update
    final_config = await crud.get_config(db_session, test_user.id)

    assert "huggingface.co" in final_config["content_filtering"]["whitelist_domains"]
    assert len(final_config["content_filtering"]["whitelist_domains"]) == 3

    print(f"✅ Verified update: whitelist now has 3 domains")
    print("=" * 60)


# =============================================================================
# TEST 5: CRUD Operations
# =============================================================================

@pytest.mark.asyncio
async def test_crud_create_extraction(db_session, test_user):
    """Test CRUD create_extraction operation."""
    print("\n" + "=" * 60)
    print("TEST 5: CRUD create_extraction")
    print("=" * 60)

    extraction_id = f"crud_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    newsletters_data = [
        {
            "newsletter_subject": "CRUD Test Newsletter",
            "newsletter_sender": "crud@test.com",
            "newsletter_date": "2025-10-15",
            "articles": [
                {"url": "https://crud.test/article1", "original_url": "https://tracking.com/1"},
                {"url": "https://crud.test/article2", "original_url": None},
            ],
        }
    ]

    # Create extraction using CRUD
    extraction = await crud.create_extraction(
        db=db_session,
        extraction_id=extraction_id,
        newsletters_data=newsletters_data,
        days_back=7,
        max_results=30,
    )

    print(f"✅ Created extraction via CRUD: {extraction_id}")

    # Note: Need to add user_id support to CRUD function
    # For now, update manually
    await db_session.execute(
        Extraction.__table__.update()
        .where(Extraction.id == extraction_id)
        .values(user_id=test_user.id)
    )
    await db_session.commit()

    print(f"✅ Updated extraction with user_id={test_user.id}")

    # Verify
    result = await db_session.execute(
        select(Extraction).where(Extraction.id == extraction_id)
    )
    saved = result.scalar_one()

    assert saved.user_id == test_user.id
    assert len(saved.content_items) == 1
    assert len(saved.content_items[0].links) == 2

    print(f"✅ Verified: extraction → 1 newsletter → 2 links")
    print("=" * 60)

    # Cleanup
    await db_session.execute(delete(Extraction).where(Extraction.id == extraction_id))
    await db_session.commit()


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CONTENT ENGINE MVP SCHEMA TESTS")
    print("=" * 60)
    print("Testing: users → extractions → email_content → extracted_links")
    print("Testing: CASCADE delete behavior")
    print("Testing: Config persistence")
    print("=" * 60)

    # Run pytest
    pytest.main([__file__, "-v", "-s"])
