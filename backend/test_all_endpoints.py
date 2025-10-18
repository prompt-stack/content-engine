#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Script

Tests all Content Engine API endpoints systematically.
Run with: python3 test_all_endpoints.py
"""

import requests
import json
from typing import Dict, List, Tuple
from datetime import datetime

API_BASE = "http://localhost:9765"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class EndpointTester:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def test(self, method: str, endpoint: str, data=None, expected_status=200, name=None):
        """Test a single endpoint"""
        url = f"{API_BASE}{endpoint}"
        test_name = name or f"{method} {endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status

            result = {
                "name": test_name,
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": success,
                "response_time": response.elapsed.total_seconds()
            }

            if success:
                self.passed += 1
                print(f"{GREEN}✓{RESET} {test_name} ({response.status_code}) - {response.elapsed.total_seconds():.2f}s")
            else:
                self.failed += 1
                print(f"{RED}✗{RESET} {test_name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"  Error: {error_detail}")
                except:
                    print(f"  Response: {response.text[:200]}")

            self.results.append(result)
            return success, response

        except requests.exceptions.ConnectionError:
            self.failed += 1
            print(f"{RED}✗{RESET} {test_name} - Connection failed (Is the API running?)")
            return False, None
        except Exception as e:
            self.failed += 1
            print(f"{RED}✗{RESET} {test_name} - {str(e)}")
            return False, None

    def skip(self, name: str, reason: str):
        """Skip a test"""
        self.skipped += 1
        print(f"{YELLOW}⊘{RESET} {name} - Skipped: {reason}")

    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed + self.skipped
        print(f"\n{'='*60}")
        print(f"Test Summary")
        print(f"{'='*60}")
        print(f"{GREEN}Passed:{RESET}  {self.passed}/{total}")
        print(f"{RED}Failed:{RESET}  {self.failed}/{total}")
        print(f"{YELLOW}Skipped:{RESET} {self.skipped}/{total}")
        print(f"{'='*60}\n")


def main():
    print(f"\n{BLUE}Content Engine - Comprehensive API Testing{RESET}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base: {API_BASE}\n")

    tester = EndpointTester()

    # ========================================================================
    # 1. Health & System
    # ========================================================================
    print(f"\n{BLUE}1. Health & System Endpoints{RESET}")
    print("-" * 60)
    tester.test("GET", "/", name="Root health check")
    tester.test("GET", "/health", name="Detailed health check")

    # ========================================================================
    # 2. Extractors
    # ========================================================================
    print(f"\n{BLUE}2. Extractor Endpoints{RESET}")
    print("-" * 60)

    # Test YouTube extractor
    youtube_data = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    success, response = tester.test("POST", "/api/extract/youtube", data=youtube_data,
                                      name="Extract YouTube video")

    # Test Reddit extractor
    reddit_data = {"url": "https://www.reddit.com/r/programming/comments/test/", "max_comments": 5}
    tester.test("POST", "/api/extract/reddit", data=reddit_data,
                name="Extract Reddit post", expected_status=400)  # Expect 400 for fake URL

    # Test TikTok extractor
    tiktok_data = {"url": "https://www.tiktok.com/@test/video/1234567890"}
    tester.test("POST", "/api/extract/tiktok", data=tiktok_data,
                name="Extract TikTok video", expected_status=400)

    # Test Article extractor
    article_data = {"url": "https://example.com/article"}
    tester.test("POST", "/api/extract/article", data=article_data,
                name="Extract article")

    # Test Auto detector
    auto_data = {"url": "https://www.youtube.com/watch?v=test"}
    tester.test("POST", "/api/extract/auto", data=auto_data,
                name="Auto-detect and extract")

    # ========================================================================
    # 3. Captures (Content Vault)
    # ========================================================================
    print(f"\n{BLUE}3. Capture/Vault Endpoints{RESET}")
    print("-" * 60)

    # Test capture text
    capture_data = {
        "title": "Test Capture",
        "content": "This is a test capture from automated testing",
        "meta": {"source": "automated-test", "timestamp": datetime.now().isoformat()}
    }
    success, capture_response = tester.test("POST", "/api/capture/text", data=capture_data,
                                             name="Create capture")

    capture_id = None
    if success and capture_response:
        try:
            capture_id = capture_response.json().get("id")
        except:
            pass

    # Test list captures
    tester.test("GET", "/api/capture/list", name="List all captures")

    # Test search captures
    tester.test("GET", "/api/capture/search?q=test", name="Search captures")

    # Test get specific capture
    if capture_id:
        tester.test("GET", f"/api/capture/{capture_id}", name="Get specific capture")
    else:
        tester.skip("Get specific capture", "No capture ID from previous test")

    # Test capture count
    tester.test("GET", "/api/capture/stats/count", name="Get capture count")

    # Test delete capture (cleanup)
    if capture_id:
        tester.test("DELETE", f"/api/capture/{capture_id}", name="Delete capture")
    else:
        tester.skip("Delete capture", "No capture ID to delete")

    # ========================================================================
    # 4. LLM Processing
    # ========================================================================
    print(f"\n{BLUE}4. LLM Processing Endpoints{RESET}")
    print("-" * 60)

    tester.test("GET", "/api/llm/providers", name="List LLM providers")

    llm_data = {
        "prompt": "Say hello in one word",
        "provider": "deepseek",
        "max_tokens": 10
    }
    tester.test("POST", "/api/llm/generate", data=llm_data,
                name="Generate with LLM")

    process_data = {
        "content": "This is a test article about AI and machine learning.",
        "task": "summarize",
        "provider": "deepseek"
    }
    tester.test("POST", "/api/llm/process-content", data=process_data,
                name="Process content with LLM")

    # ========================================================================
    # 5. Media Generation
    # ========================================================================
    print(f"\n{BLUE}5. Media Generation Endpoints{RESET}")
    print("-" * 60)

    tester.test("GET", "/api/media/providers", name="List media providers")

    tester.skip("Generate image from prompt", "Requires API key and costs money")
    tester.skip("Generate image from content", "Requires API key and costs money")

    # ========================================================================
    # 6. Search
    # ========================================================================
    print(f"\n{BLUE}6. Search Endpoints{RESET}")
    print("-" * 60)

    tester.test("GET", "/api/search/capabilities", name="Get search capabilities")

    tester.skip("General search", "Requires Tavily API key")
    tester.skip("Context search", "Requires Tavily API key")
    tester.skip("Trending search", "Requires Tavily API key")
    tester.skip("Fact check", "Requires Tavily API key")
    tester.skip("News search", "Requires Tavily API key")
    tester.skip("Research search", "Requires Tavily API key")

    # ========================================================================
    # 7. Prompts
    # ========================================================================
    print(f"\n{BLUE}7. Prompts Endpoints{RESET}")
    print("-" * 60)

    tester.test("GET", "/api/prompts/list", name="List all prompts", expected_status=404)
    tester.test("GET", "/api/prompts/categories", name="List prompt categories", expected_status=404)

    # ========================================================================
    # 8. Newsletters
    # ========================================================================
    print(f"\n{BLUE}8. Newsletter Endpoints{RESET}")
    print("-" * 60)

    tester.test("GET", "/api/newsletters/digests", name="List newsletter digests")
    tester.test("GET", "/api/newsletters/resolved", name="List resolved links")
    tester.test("GET", "/api/newsletters/config", name="Get newsletter config")

    # Print summary
    tester.print_summary()

    # Save results to file
    output_file = "test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": tester.passed + tester.failed + tester.skipped,
                "passed": tester.passed,
                "failed": tester.failed,
                "skipped": tester.skipped
            },
            "results": tester.results
        }, f, indent=2)

    print(f"Results saved to: {output_file}\n")


if __name__ == "__main__":
    main()
