#!/usr/bin/env python3
"""
Test suite for content filtering logic.

Tests the core business logic that determines which URLs are accepted/rejected.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import step4_filter_content
sys.path.insert(0, str(Path(__file__).parent.parent))

from step4_filter_content import is_content_url, load_config


@pytest.fixture
def test_config():
    """Test configuration with known values."""
    return {
        'content_filtering': {
            'whitelist_domains': [
                'github.com',
                'arxiv.org',
                'techcrunch.com',
                'huggingface.co',
                'blog.google',
                'microsoft.ai',
                'openai.com',
                'warp.dev',
                'graphite.io',
            ],
            'blacklist_domains': [
                'typeform.com',
                'surveymonkey.com',
                'mailchi.mp',
            ],
            'curator_domains': [
                'alphasignal.ai',
                'therundown.ai',
                'rundown.ai',
            ],
            'content_indicators': [
                '/blog/',
                '/article/',
                '/post/',
                '/p/',
                '/status/',
                '/guides/',
            ]
        }
    }


class TestWhitelistDomains:
    """Test whitelisted domains are always accepted."""

    def test_github_repo_accepted(self, test_config):
        """GitHub repos should be accepted."""
        url = "https://github.com/karpathy/nanochat"
        assert is_content_url(url, test_config) is True

    def test_arxiv_paper_accepted(self, test_config):
        """arXiv papers should be accepted."""
        url = "https://arxiv.org/abs/2506.10943"
        assert is_content_url(url, test_config) is True

    def test_techcrunch_article_accepted(self, test_config):
        """TechCrunch articles should be accepted."""
        url = "https://techcrunch.com/2025/10/15/ai-news"
        assert is_content_url(url, test_config) is True

    def test_huggingface_collection_accepted(self, test_config):
        """HuggingFace collections should be accepted."""
        url = "https://huggingface.co/collections/Qwen/qwen3-vl-68d2a7c1b8a8afce4ebd2dbe"
        assert is_content_url(url, test_config) is True

    def test_google_blog_accepted(self, test_config):
        """Google blog posts should be accepted."""
        url = "https://blog.google/technology/google-labs/video-overviews-nano-banana/"
        assert is_content_url(url, test_config) is True

    def test_microsoft_ai_accepted(self, test_config):
        """Microsoft AI news should be accepted."""
        url = "https://microsoft.ai/news/introducing-mai-image-1"
        assert is_content_url(url, test_config) is True

    def test_openai_platform_docs_accepted(self, test_config):
        """OpenAI platform docs should be accepted."""
        url = "https://platform.openai.com/docs/guides/tools-web-search"
        assert is_content_url(url, test_config) is True

    def test_warp_dev_product_page_accepted(self, test_config):
        """Warp.dev sponsor pages should be accepted."""
        url = "https://www.warp.dev/code"
        assert is_content_url(url, test_config) is True


class TestBlacklistDomains:
    """Test blacklisted domains are always rejected."""

    def test_typeform_rejected(self, test_config):
        """Typeform surveys should be rejected."""
        url = "https://typeform.com/to/abc123"
        assert is_content_url(url, test_config) is False

    def test_surveymonkey_rejected(self, test_config):
        """SurveyMonkey surveys should be rejected."""
        url = "https://surveymonkey.com/r/survey123"
        assert is_content_url(url, test_config) is False

    def test_mailchimp_rejected(self, test_config):
        """Mailchimp links should be rejected."""
        url = "https://mailchi.mp/example/newsletter"
        assert is_content_url(url, test_config) is False


class TestCuratorDomains:
    """Test newsletter curator domains are rejected (circular reference)."""

    def test_alphasignal_homepage_rejected(self, test_config):
        """AlphaSignal homepage should be rejected."""
        url = "https://alphasignal.ai/"
        assert is_content_url(url, test_config) is False

    def test_alphasignal_email_view_rejected(self, test_config):
        """AlphaSignal email views should be rejected."""
        url = "https://alphasignal.ai/email/abc123"
        assert is_content_url(url, test_config) is False

    def test_therundown_article_rejected(self, test_config):
        """The Rundown's own articles should be rejected."""
        url = "https://www.therundown.ai/p/chatgpt-to-go-18-plus"
        assert is_content_url(url, test_config) is False

    def test_rundown_tools_page_rejected(self, test_config):
        """Rundown.ai tools pages should be rejected."""
        url = "https://www.rundown.ai/tools"
        assert is_content_url(url, test_config) is False

    def test_app_rundown_guides_rejected(self, test_config):
        """App subdomain guides should be rejected."""
        url = "https://app.therundown.ai/guides/automate-market-research"
        assert is_content_url(url, test_config) is False


class TestContentIndicators:
    """Test URLs with content indicators in path."""

    def test_blog_path_accepted(self, test_config):
        """URLs with /blog/ should be accepted."""
        url = "https://example.com/blog/my-post"
        assert is_content_url(url, test_config) is True

    def test_article_path_accepted(self, test_config):
        """URLs with /article/ should be accepted."""
        url = "https://example.com/article/news-story"
        assert is_content_url(url, test_config) is True

    def test_post_path_accepted(self, test_config):
        """URLs with /post/ should be accepted."""
        url = "https://example.com/post/123"
        assert is_content_url(url, test_config) is True

    def test_substack_p_path_accepted(self, test_config):
        """Substack /p/ paths should be accepted."""
        url = "https://newsletter.substack.com/p/my-article"
        assert is_content_url(url, test_config) is True

    def test_twitter_status_accepted(self, test_config):
        """Twitter status URLs should be accepted."""
        url = "https://x.com/sama/status/1978129344598827128"
        assert is_content_url(url, test_config) is True

    def test_guides_path_accepted(self, test_config):
        """URLs with /guides/ should be accepted."""
        url = "https://example.com/guides/getting-started"
        assert is_content_url(url, test_config) is True


class TestSpecialCases:
    """Test special cases and edge conditions."""

    def test_auth_page_rejected(self, test_config):
        """Auth/login pages should be rejected."""
        url = "https://accounts.google.com/signin/identifier"
        assert is_content_url(url, test_config) is False

    def test_google_ai_studio_welcome_accepted(self, test_config):
        """Google AI Studio welcome page should be accepted (not auth)."""
        url = "https://aistudio.google.com/welcome"
        # Note: This is whitelisted because aistudio.google.com is in whitelist
        # But let's check if it's actually in the test config
        # For this test, we'll add it temporarily
        test_config['content_filtering']['whitelist_domains'].append('aistudio.google.com')
        assert is_content_url(url, test_config) is True

    def test_twitter_profile_rejected(self, test_config):
        """Twitter profiles (not tweets) should be rejected."""
        url = "https://x.com/AlphaSignalAI"
        assert is_content_url(url, test_config) is False

    def test_github_repo_with_path_accepted(self, test_config):
        """GitHub repos with specific file paths should be accepted."""
        url = "https://github.com/microsoft/ai-agents-for-beginners/tree/main/14-microsoft-agent-framework"
        assert is_content_url(url, test_config) is True

    def test_github_homepage_rejected(self, test_config):
        """GitHub homepage should be rejected (no user/repo)."""
        url = "https://github.com"
        assert is_content_url(url, test_config) is False

    def test_youtube_video_rejected_without_indicator(self, test_config):
        """YouTube videos need to be on whitelist or have indicators."""
        url = "https://www.youtube.com/watch?v=abc123"
        # YouTube is not whitelisted in test config, and /watch?v= might not be an indicator
        # Let's check the actual behavior
        result = is_content_url(url, test_config)
        # This test documents current behavior
        assert result is False  # Not whitelisted and no path indicators

    def test_empty_url_rejected(self, test_config):
        """Empty URLs should be rejected."""
        assert is_content_url("", test_config) is False
        assert is_content_url(None, test_config) is False


class TestConfigLoading:
    """Test config loading functionality."""

    def test_load_config_returns_dict(self):
        """load_config() should return a dictionary."""
        config = load_config()
        assert isinstance(config, dict)

    def test_config_has_content_filtering(self):
        """Config should have content_filtering section."""
        config = load_config()
        assert 'content_filtering' in config

    def test_config_has_required_fields(self):
        """Config should have all required filtering fields."""
        config = load_config()
        filtering = config['content_filtering']
        assert 'whitelist_domains' in filtering
        assert 'blacklist_domains' in filtering
        assert 'curator_domains' in filtering
        assert 'content_indicators' in filtering

    def test_config_fields_are_lists(self):
        """Config fields should be lists."""
        config = load_config()
        filtering = config['content_filtering']
        assert isinstance(filtering['whitelist_domains'], list)
        assert isinstance(filtering['blacklist_domains'], list)
        assert isinstance(filtering['curator_domains'], list)
        assert isinstance(filtering['content_indicators'], list)


class TestRealWorldURLs:
    """Test real URLs from actual newsletter extractions."""

    def test_real_accepted_urls(self, test_config):
        """Test URLs that should be accepted from real newsletters."""
        accepted_urls = [
            "https://github.com/karpathy/nanochat",
            "https://arxiv.org/abs/2506.10943",
            "https://blog.google/technology/google-labs/video-overviews-nano-banana/",
            "https://x.com/sama/status/1978129344598827128",
            "https://huggingface.co/collections/Qwen/qwen3-vl-68d2a7c1b8a8afce4ebd2dbe",
        ]

        # Add missing domains to test config
        test_config['content_filtering']['whitelist_domains'].extend([
            'x.com',
            'twitter.com'
        ])

        for url in accepted_urls:
            assert is_content_url(url, test_config) is True, f"URL should be accepted: {url}"

    def test_real_rejected_urls(self, test_config):
        """Test URLs that should be rejected from real newsletters."""
        rejected_urls = [
            "https://alphasignal.ai/email/abc123",
            "https://www.therundown.ai/subscribe",
            "https://typeform.com/to/survey",
            "https://accounts.google.com/signin",
            "https://x.com/AlphaSignalAI",  # Profile, not tweet
        ]

        for url in rejected_urls:
            assert is_content_url(url, test_config) is False, f"URL should be rejected: {url}"


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
