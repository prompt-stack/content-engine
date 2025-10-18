#!/usr/bin/env python3.11
"""Test config API endpoints with database persistence."""

import requests
import json

API_BASE = "http://localhost:9765/api/newsletters"

def test_config_persistence():
    """Test GET → UPDATE → GET workflow to verify database persistence."""

    print("=" * 60)
    print("TESTING CONFIG API PERSISTENCE")
    print("=" * 60)

    # Step 1: GET current config
    print("\n1️⃣  GET /config - Fetching current config...")
    response = requests.get(f"{API_BASE}/config")
    response.raise_for_status()
    config = response.json()

    original_whitelist = config['content_filtering']['whitelist_domains'].copy()
    print(f"✅ Current whitelist has {len(original_whitelist)} domains")
    print(f"   Original whitelist: {original_whitelist[:3]}...")

    # Step 2: UPDATE config (add a test domain)
    print("\n2️⃣  PUT /config - Adding test domain 'TESTING_UPDATE.com'...")
    config['content_filtering']['whitelist_domains'].append('TESTING_UPDATE.com')

    response = requests.put(
        f"{API_BASE}/config",
        json=config,
        headers={'Content-Type': 'application/json'}
    )
    response.raise_for_status()
    result = response.json()
    print(f"✅ {result['message']}")

    # Step 3: GET config again to verify update persisted
    print("\n3️⃣  GET /config - Verifying update persisted to database...")
    response = requests.get(f"{API_BASE}/config")
    response.raise_for_status()
    updated_config = response.json()

    updated_whitelist = updated_config['content_filtering']['whitelist_domains']
    print(f"✅ Updated whitelist has {len(updated_whitelist)} domains")

    if 'TESTING_UPDATE.com' in updated_whitelist:
        print("✅ TEST PASSED: 'TESTING_UPDATE.com' found in database!")
    else:
        print("❌ TEST FAILED: 'TESTING_UPDATE.com' not found in database")
        return False

    # Step 4: Cleanup - restore original config
    print("\n4️⃣  PUT /config - Restoring original config...")
    config['content_filtering']['whitelist_domains'] = original_whitelist
    response = requests.put(
        f"{API_BASE}/config",
        json=config,
        headers={'Content-Type': 'application/json'}
    )
    response.raise_for_status()
    print("✅ Original config restored")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Database persistence working!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        test_config_persistence()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
