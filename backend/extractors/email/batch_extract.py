#!/usr/bin/env python3
"""
Batch Content Extractor - Pass resolved newsletter links through content-engine API
Preserves newsletter context (source, date, links)
"""

import json
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


def read_resolved_links(file_path: Path) -> List[Dict]:
    """Read resolved links JSON with newsletter context"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_content(url: str, api_url: str = "http://localhost:9765/api/extract/auto") -> Optional[Dict]:
    """
    Extract content from URL using content-engine API

    Args:
        url: URL to extract content from
        api_url: Content-engine API endpoint

    Returns:
        Extracted content dict or None if failed
    """
    try:
        response = requests.post(
            api_url,
            json={"url": url},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"    ❌ API error {response.status_code}: {url[:60]}...")
            return None

    except requests.exceptions.Timeout:
        print(f"    ⏱️  Timeout: {url[:60]}...")
        return None
    except requests.exceptions.ConnectionError:
        print(f"    ❌ Connection error (is content-engine running?): {url[:60]}...")
        return None
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:50]}")
        return None


def save_article(article: Dict, output_dir: Path, index: int):
    """Save individual article as markdown file"""

    # Create safe filename from title or URL
    title = article.get('metadata', {}).get('title', f'article_{index}')
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title[:60]  # Limit length

    filename = f"{index:03d}_{safe_title}.md"
    file_path = output_dir / filename

    # Format as markdown
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"# {article.get('metadata', {}).get('title', 'Untitled')}\n\n")

        # Metadata
        metadata = article.get('metadata', {})
        f.write(f"**Source**: {metadata.get('url', 'Unknown')}\n")
        f.write(f"**Author**: {metadata.get('author', 'Unknown')}\n")
        f.write(f"**Published**: {metadata.get('published_date', 'Unknown')}\n")

        if metadata.get('description'):
            f.write(f"\n**Description**: {metadata['description']}\n")

        f.write(f"\n---\n\n")

        # Content
        content = article.get('content', {})
        if content.get('markdown'):
            f.write(content['markdown'])
        elif content.get('text'):
            f.write(content['text'])
        else:
            f.write("*No content extracted*\n")

        # Tags
        if metadata.get('tags'):
            f.write(f"\n\n---\n**Tags**: {', '.join(metadata['tags'])}\n")

    return file_path


def batch_extract(input_file: Path, api_url: str = "http://localhost:9765/api/extract/auto", delay: float = 1.0):
    """
    Batch extract content from resolved newsletter links JSON
    Preserves newsletter organization (source, date, articles)

    Args:
        input_file: Path to resolved_links_*.json file
        api_url: Content-engine API endpoint
        delay: Delay between requests in seconds
    """
    print(f"📄 Reading newsletters from: {input_file.name}\n")

    # Read newsletters with resolved links
    newsletters = read_resolved_links(input_file)

    if not newsletters:
        print("❌ No newsletters found in file")
        return

    total_links = sum(n['link_count'] for n in newsletters)
    print(f"✅ Found {len(newsletters)} newsletters with {total_links} article links\n")

    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(__file__).parent / "output" / f"newsletter_digest_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each newsletter
    processed_newsletters = []
    total_successful = 0
    total_failed = 0

    for newsletter_idx, newsletter in enumerate(newsletters, 1):
        subject = newsletter['newsletter_subject']
        sender = newsletter['newsletter_sender']
        date = newsletter['newsletter_date']
        links = newsletter['links']

        print(f"\n{'='*80}")
        print(f"📧 Newsletter {newsletter_idx}/{len(newsletters)}: {subject[:60]}")
        print(f"   From: {sender}")
        print(f"   Date: {date}")
        print(f"   Links: {len(links)}\n")

        # Extract each article from this newsletter
        extracted_articles = []
        failed_articles = []

        for link_idx, link_obj in enumerate(links, 1):
            url = link_obj['url']
            print(f"   [{link_idx}/{len(links)}] Extracting: {url[:60]}...")

            # Extract content
            article = extract_content(url, api_url)

            if article and article.get('content'):
                try:
                    # Save article with newsletter context
                    article['newsletter_context'] = {
                        'subject': subject,
                        'sender': sender,
                        'date': date
                    }

                    file_path = save_article(article, output_dir, f"{newsletter_idx}_{link_idx}")

                    extracted_articles.append({
                        'url': url,
                        'title': article.get('metadata', {}).get('title', 'Untitled'),
                        'file': file_path.name,
                        'original_url': link_obj.get('original_url')
                    })
                    print(f"       ✅ {article.get('metadata', {}).get('title', 'Untitled')[:50]}")
                    total_successful += 1
                except Exception as e:
                    print(f"       ❌ Error saving: {str(e)[:40]}")
                    failed_articles.append({'url': url, 'error': str(e)[:50]})
                    total_failed += 1
            else:
                print(f"       ❌ Extraction failed")
                failed_articles.append({'url': url, 'error': 'Extraction failed'})
                total_failed += 1

            # Delay between requests
            if link_idx < len(links):
                time.sleep(delay)

        # Save newsletter summary
        processed_newsletters.append({
            'newsletter_subject': subject,
            'newsletter_sender': sender,
            'newsletter_date': date,
            'total_links': len(links),
            'successful': len(extracted_articles),
            'failed': len(failed_articles),
            'articles': extracted_articles,
            'failures': failed_articles
        })

    # Save manifest with newsletter organization
    manifest_file = output_dir / "manifest.json"
    manifest = {
        'timestamp': datetime.now().isoformat(),
        'input_file': str(input_file),
        'total_newsletters': len(newsletters),
        'total_links': total_links,
        'total_successful': total_successful,
        'total_failed': total_failed,
        'newsletters': processed_newsletters
    }

    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Create organized digest by newsletter
    digest_file = output_dir / "digest.md"
    with open(digest_file, 'w', encoding='utf-8') as f:
        f.write(f"# Newsletter Article Digest\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Newsletters**: {len(newsletters)}\n")
        f.write(f"**Articles Extracted**: {total_successful}/{total_links}\n\n")
        f.write("---\n\n")

        for newsletter_data in processed_newsletters:
            if newsletter_data['successful'] > 0:
                f.write(f"## 📧 {newsletter_data['newsletter_subject']}\n\n")
                f.write(f"**From**: {newsletter_data['newsletter_sender']}\n")
                f.write(f"**Date**: {newsletter_data['newsletter_date']}\n")
                f.write(f"**Articles**: {newsletter_data['successful']}/{newsletter_data['total_links']}\n\n")
                f.write("---\n\n")

                for article_info in newsletter_data['articles']:
                    article_file = output_dir / article_info['file']
                    if article_file.exists():
                        with open(article_file, 'r', encoding='utf-8') as af:
                            f.write(af.read())
                            f.write("\n\n---\n\n")

    # Print summary
    print(f"\n{'='*80}")
    print(f"📊 Final Summary:\n")
    print(f"  📧 Newsletters processed: {len(newsletters)}")
    print(f"  🔗 Total article links: {total_links}")
    print(f"  ✅ Successfully extracted: {total_successful}")
    print(f"  ❌ Failed: {total_failed}\n")

    for newsletter_data in processed_newsletters:
        print(f"  📧 {newsletter_data['newsletter_subject'][:50]}")
        print(f"     {newsletter_data['successful']}/{newsletter_data['total_links']} articles extracted")

    print(f"\n📂 Files saved:")
    print(f"   • digest.md - Complete digest organized by newsletter")
    print(f"   • manifest.json - Extraction details and context")
    print(f"   • {total_successful} individual article files (.md)\n")
    print(f"📍 Location: {output_dir.absolute()}\n")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Batch extract content from resolved newsletter links')
    parser.add_argument('--input', type=str, required=True, help='Input JSON file (resolved_links_*.json)')
    parser.add_argument('--api', type=str, default='http://localhost:9765/api/extract/auto', help='Content-engine API URL')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')

    args = parser.parse_args()

    input_file = Path(args.input)

    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        exit(1)

    if not input_file.suffix == '.json':
        print(f"❌ Input must be a JSON file (resolved_links_*.json)")
        print(f"   Use resolve_links.py to generate this file first")
        exit(1)

    batch_extract(input_file, api_url=args.api, delay=args.delay)
