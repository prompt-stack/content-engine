"""
Example: Content Enrichment Workflow with Tavily Search
Demonstrates the complete pipeline: Extract → Research → Summarize → Image

This example shows how Tavily search adds research capabilities to content processing.
"""

import requests
import json


class ContentEngineWithSearch:
    def __init__(self, base_url="http://localhost:9765"):
        self.base_url = base_url

    def enrich_content_with_research(self, url):
        """
        Complete workflow with research step:
        1. Extract content from URL
        2. Research context using Tavily
        3. Summarize with context
        4. Generate tags
        5. Generate featured image
        """

        print(f"🎯 Starting content enrichment with research...\n")

        # Step 1: Extract content
        print("📥 Step 1: Extracting content...")
        extract = requests.post(
            f"{self.base_url}/api/extract/auto",
            json={"url": url}
        ).json()

        title = extract.get("title", "")
        content = extract.get("content", "")
        print(f"✅ Extracted: {title}\n")

        # Step 2: Research context (NEW with Tavily!)
        print("🔍 Step 2: Researching additional context...")

        # Generate research query from title
        research_query = f"background information about: {title}"

        search_results = requests.post(
            f"{self.base_url}/api/search/search",
            json={
                "query": research_query,
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True
            }
        ).json()

        print(f"✅ Found {search_results['total_results']} research sources")

        # Combine original content with research findings
        research_context = "\n\n".join([
            f"Source: {r['title']}\n{r['content'][:200]}..."
            for r in search_results['results'][:3]
        ])

        enriched_content = f"{content}\n\n--- Research Context ---\n{research_context}"
        print(f"✅ Content enriched with research\n")

        # Step 3: Summarize with context
        print("🤖 Step 3: Summarizing with context...")
        summary = requests.post(
            f"{self.base_url}/api/llm/process-content",
            json={
                "content": enriched_content,
                "task": "summarize",
                "provider": "deepseek",
                "max_tokens": 200
            }
        ).json()

        print(f"✅ Summary generated\n")

        # Step 4: Generate tags
        print("🏷️  Step 4: Generating tags...")
        tags = requests.post(
            f"{self.base_url}/api/llm/process-content",
            json={
                "content": content,
                "task": "generate_tags",
                "provider": "anthropic",
                "max_tokens": 100
            }
        ).json()

        print(f"✅ Tags generated\n")

        # Step 5: Generate image
        print("🎨 Step 5: Generating featured image...")
        image = requests.post(
            f"{self.base_url}/api/media/generate-from-content",
            json={
                "content": summary["result"],
                "provider": "openai"
            }
        ).json()

        print(f"✅ Image generated\n")

        # Return enriched package
        result = {
            "original": {
                "title": title,
                "url": url,
                "content_length": len(content)
            },
            "research": {
                "sources_found": search_results["total_results"],
                "top_sources": [
                    {"title": r["title"], "url": r["url"]}
                    for r in search_results["results"][:3]
                ]
            },
            "summary": summary["result"],
            "tags": tags["result"],
            "image": {
                "url": image["image_url"],
                "prompt": image.get("generated_prompt", "")
            }
        }

        return result

    def fact_check_content(self, url):
        """
        Extract content and fact-check claims
        """
        print(f"🔎 Fact-checking content from URL...\n")

        # Extract content
        print("📥 Extracting content...")
        extract = requests.post(
            f"{self.base_url}/api/extract/auto",
            json={"url": url}
        ).json()

        content = extract.get("content", "")

        # Extract key claims
        print("🤖 Extracting claims...")
        claims = requests.post(
            f"{self.base_url}/api/llm/process-content",
            json={
                "content": content,
                "task": "extract_key_points",
                "provider": "openai",
                "max_tokens": 200
            }
        ).json()

        # Fact-check the claims
        print("✅ Fact-checking claims...")
        fact_check = requests.post(
            f"{self.base_url}/api/search/fact-check",
            json={
                "claim": claims["result"],
                "max_results": 5
            }
        ).json()

        print(f"✅ Found {fact_check['total_sources']} verification sources\n")

        return {
            "original_url": url,
            "claims_extracted": claims["result"],
            "verification_sources": fact_check["sources"],
            "total_sources": fact_check["total_sources"]
        }

    def discover_trending_content(self, topic, platforms=None):
        """
        Discover trending content on specific platforms
        """
        print(f"📊 Discovering trending content about '{topic}'...\n")

        trending = requests.post(
            f"{self.base_url}/api/search/trending",
            json={
                "topic": topic,
                "platforms": platforms or ["reddit", "twitter", "youtube"],
                "max_results": 10
            }
        ).json()

        print(f"✅ Found {trending['total_results']} trending items\n")

        # Summarize the trend
        trend_content = "\n".join([
            f"{r['title']}: {r['content'][:100]}..."
            for r in trending["results"][:5]
        ])

        summary = requests.post(
            f"{self.base_url}/api/llm/process-content",
            json={
                "content": f"Trending content about {topic}:\n\n{trend_content}",
                "task": "summarize",
                "provider": "deepseek",
                "max_tokens": 150
            }
        ).json()

        return {
            "topic": topic,
            "platforms_searched": platforms,
            "trending_items": trending["results"],
            "trend_summary": summary["result"]
        }


# Example Usage
if __name__ == "__main__":
    client = ContentEngineWithSearch()

    print("=" * 60)
    print("🚀 Content Engine + Tavily Search Examples")
    print("=" * 60)
    print()

    # Example 1: Full enrichment with research
    print("📋 Example 1: Content Enrichment with Research")
    print("-" * 60)
    result1 = client.enrich_content_with_research(
        "https://www.tiktok.com/@hoffdigital/video/7535517761863224606"
    )

    print("📦 RESULT:")
    print(json.dumps(result1, indent=2))
    print("\n")

    # Example 2: Fact-checking
    print("📋 Example 2: Fact-Check Content")
    print("-" * 60)
    result2 = client.fact_check_content(
        "https://www.reddit.com/r/technology/comments/example"
    )

    print("📦 RESULT:")
    print(json.dumps(result2, indent=2))
    print("\n")

    # Example 3: Discover trending
    print("📋 Example 3: Discover Trending Content")
    print("-" * 60)
    result3 = client.discover_trending_content(
        topic="artificial intelligence",
        platforms=["reddit", "twitter"]
    )

    print("📦 RESULT:")
    print(json.dumps(result3, indent=2))
    print("\n")

    print("=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)


"""
KEY BENEFITS OF TAVILY INTEGRATION:

1. Content Research
   - Automatically find background information
   - Add context to extracted content
   - Enrich articles with authoritative sources

2. Fact-Checking
   - Verify claims in extracted content
   - Find authoritative verification sources
   - Build trust in content

3. Trend Discovery
   - Monitor trending topics across platforms
   - Discover viral content
   - Track discussions

4. Workflow Enhancement
   Before: URL → Extract → Process → Image
   After:  URL → Extract → Research → Process → Image
           ✅ Much more valuable output!

COST COMPARISON:
- Without Tavily: Basic extraction + processing
- With Tavily: Research-enhanced, fact-checked, context-rich content
- Additional cost: ~$0.001 per search (negligible)
- Value increase: 10x more useful output

USE CASES:
1. Newsletter Creation: Extract + research sources + summarize
2. Content Verification: Extract + fact-check claims
3. Trend Monitoring: Discover trending + summarize trends
4. Research Reports: Search + extract + synthesize
"""