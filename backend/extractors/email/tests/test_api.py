#!/usr/bin/env python3
"""
Test suite for newsletter API endpoints.

Tests the FastAPI endpoints for config management and URL testing.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "version" in data

    def test_health_endpoint(self):
        """Test health endpoint returns detailed status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "features" in data


class TestConfigEndpoints:
    """Test configuration API endpoints."""

    def test_get_config(self):
        """Test getting current configuration."""
        response = client.get("/api/newsletters/config")
        assert response.status_code == 200

        data = response.json()
        assert "content_filtering" in data

        filtering = data["content_filtering"]
        assert "whitelist_domains" in filtering
        assert "blacklist_domains" in filtering
        assert "curator_domains" in filtering
        assert "content_indicators" in filtering

    def test_config_structure(self):
        """Test config has correct structure and types."""
        response = client.get("/api/newsletters/config")
        data = response.json()

        filtering = data["content_filtering"]

        # Check types
        assert isinstance(filtering["whitelist_domains"], list)
        assert isinstance(filtering["blacklist_domains"], list)
        assert isinstance(filtering["curator_domains"], list)
        assert isinstance(filtering["content_indicators"], list)

        # Check non-empty
        assert len(filtering["whitelist_domains"]) > 0
        assert len(filtering["blacklist_domains"]) > 0
        assert len(filtering["curator_domains"]) > 0
        assert len(filtering["content_indicators"]) > 0


class TestURLTesting:
    """Test URL filtering test endpoint."""

    def test_test_whitelisted_url(self):
        """Test URL on whitelist is accepted."""
        response = client.post(
            "/api/newsletters/config/test-url",
            json={"url": "https://github.com/karpathy/nanochat"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["url"] == "https://github.com/karpathy/nanochat"
        assert data["is_valid"] is True
        assert "accepted" in data["reason"].lower()

    def test_test_blacklisted_url(self):
        """Test URL on blacklist is rejected."""
        response = client.post(
            "/api/newsletters/config/test-url",
            json={"url": "https://typeform.com/to/survey"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["url"] == "https://typeform.com/to/survey"
        assert data["is_valid"] is False
        assert "blacklist" in data["reason"].lower()

    def test_test_curator_url(self):
        """Test curator URL is rejected."""
        response = client.post(
            "/api/newsletters/config/test-url",
            json={"url": "https://www.therundown.ai/p/article"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is False
        assert "curator" in data["reason"].lower()

    def test_test_url_with_content_indicator(self):
        """Test URL with content indicator is accepted."""
        response = client.post(
            "/api/newsletters/config/test-url",
            json={"url": "https://example.com/blog/my-post"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is True

    def test_test_url_missing_url_field(self):
        """Test endpoint with missing URL field returns error."""
        response = client.post(
            "/api/newsletters/config/test-url",
            json={}
        )
        assert response.status_code == 422  # Validation error

    def test_response_structure(self):
        """Test response has correct structure."""
        response = client.post(
            "/api/newsletters/config/test-url",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "url" in data
        assert "is_valid" in data
        assert "reason" in data

        # Check types
        assert isinstance(data["url"], str)
        assert isinstance(data["is_valid"], bool)
        assert isinstance(data["reason"], str)


class TestRealWorldScenarios:
    """Test real-world scenarios from production."""

    def test_batch_url_testing(self):
        """Test multiple URLs like a user would."""
        test_urls = [
            ("https://github.com/microsoft/ai-agents", True),
            ("https://arxiv.org/abs/2506.10943", True),
            ("https://alphasignal.ai/email/abc", False),
            ("https://typeform.com/to/survey", False),
            ("https://blog.example.com/post/my-article", True),  # Need full path to match /post/
        ]

        for url, expected_valid in test_urls:
            response = client.post(
                "/api/newsletters/config/test-url",
                json={"url": url}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] == expected_valid, \
                f"URL {url} should be {'valid' if expected_valid else 'invalid'}"

    def test_production_accepted_urls(self):
        """Test URLs that were accepted in production."""
        production_urls = [
            "https://github.com/karpathy/nanochat",
            "https://huggingface.co/collections/Qwen/qwen3-vl",
            "https://www.ai21.com/blog/introducing-jamba-reasoning-3b/",
            "https://blog.google/technology/google-labs/video-overviews-nano-banana/",
            "https://microsoft.ai/news/introducing-mai-image-1",
        ]

        for url in production_urls:
            response = client.post(
                "/api/newsletters/config/test-url",
                json={"url": url}
            )
            data = response.json()
            assert data["is_valid"] is True, \
                f"Production URL should be valid: {url}"

    def test_production_rejected_urls(self):
        """Test URLs that were rejected in production."""
        rejected_urls = [
            "https://alphasignal.ai/email/05be88743bf5d704",
            "https://www.therundown.ai/subscribe",
            "https://typeform.com/to/survey",
            "https://accounts.google.com/signin",
        ]

        for url in rejected_urls:
            response = client.post(
                "/api/newsletters/config/test-url",
                json={"url": url}
            )
            data = response.json()
            assert data["is_valid"] is False, \
                f"Production URL should be rejected: {url}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
