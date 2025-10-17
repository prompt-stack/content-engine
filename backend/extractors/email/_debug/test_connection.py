#!/usr/bin/env python3
"""
Test script to verify Gmail API connection
"""

from gmail_extractor import GmailExtractor


def test_connection():
    """Test basic Gmail API connection"""
    print("=" * 50)
    print("Gmail Newsletter Extractor - Connection Test")
    print("=" * 50)

    try:
        # Initialize extractor
        print("\n1. Initializing extractor...")
        extractor = GmailExtractor()
        
        # Get user profile
        print("\n2. Getting user profile...")
        profile = extractor.get_user_profile()
        
        if profile:
            print(f"   ✅ Successfully connected!")
            print(f"   📧 Email: {profile.get('emailAddress')}")
            print(f"   📊 Total messages: {profile.get('messagesTotal')}")
            print(f"   📈 Total threads: {profile.get('threadsTotal')}")
            print(f"   💾 History ID: {profile.get('historyId')}")
        
        # Try a simple search
        print("\n3. Testing newsletter search (last 3 days, max 5 results)...")
        newsletters = extractor.search_newsletters(
            days_back=3,
            max_results=5
        )
        
        if newsletters:
            print(f"   ✅ Found {len(newsletters)} newsletters:")
            for i, newsletter in enumerate(newsletters[:3], 1):
                print(f"      {i}. {newsletter['subject'][:50]}...")
                print(f"         From: {newsletter['sender_email']}")
        else:
            print("   ℹ️  No newsletters found (this might be normal)")
        
        print("\n✅ All tests passed! The extractor is working correctly.")
        print("\nYou can now run:")
        print("  python extract_newsletters.py --help")
        print("to see all available options.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure credentials.json is in this directory")
        print("2. Delete token.pickle if it exists and try again")
        print("3. Check that Gmail API is enabled in Google Cloud Console")


if __name__ == "__main__":
    test_connection()
