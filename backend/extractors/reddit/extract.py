#!/usr/bin/env python3
"""
Reddit Extractor Python Wrapper
Wraps the Node.js Reddit extractor for integration with Content Hub API
"""

import json
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from url_resolver import (
    is_short_link,
    is_canonical_permalink,
    extract_subreddit_from_short_link,
    resolve_reddit_short_link
)

def extract_reddit(url: str, title: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract Reddit post and comments using Node.js extractor

    Args:
        url: Reddit post URL (can be short link or canonical permalink)
        title: Post title (REQUIRED if url is a short link)

    Returns:
        Dictionary with extraction results
    """
    try:
        # Handle short links - try redirect first, search as fallback
        if is_short_link(url):
            # Method 1: Try following the redirect directly (fastest, free, but can be blocked)
            redirect_worked = False
            try:
                # Use multiple User-Agent strategies to avoid blocking
                user_agents = [
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'python-requests/2.31.0'
                ]

                for ua in user_agents:
                    try:
                        headers = {'User-Agent': ua}
                        response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
                        if response.status_code == 200 and is_canonical_permalink(response.url):
                            url = response.url.split('?')[0].rstrip('/')
                            print(f"✅ Resolved short link via redirect: {url}")
                            redirect_worked = True
                            break
                    except:
                        continue

                if not redirect_worked:
                    raise Exception("All redirect attempts failed or were blocked")

            except Exception as redirect_error:
                # Method 2: Use search API as fallback (requires title)
                print(f"⚠️  Redirect method failed: {redirect_error}")

                if not title:
                    return {
                        'success': False,
                        'error': (
                            'Reddit blocked the redirect. Please provide the post title so we can search for it.\n'
                            f'Error: {redirect_error}'
                        ),
                        'title': 'Reddit Post',
                        'url': url
                    }

                subreddit = extract_subreddit_from_short_link(url)
                if not subreddit:
                    return {
                        'success': False,
                        'error': 'Could not extract subreddit from short link',
                        'title': 'Reddit Post',
                        'url': url
                    }

                try:
                    url = resolve_reddit_short_link(title, subreddit)
                    print(f"✅ Resolved short link via search API: {url}")
                except ValueError as search_error:
                    return {
                        'success': False,
                        'error': (
                            f'Could not resolve short link.\n'
                            f'Redirect: {redirect_error}\n'
                            f'Search: {search_error}\n'
                            f'The post might be too recent or in a private subreddit.'
                        ),
                        'title': title,
                        'url': url
                    }

        # Try following redirects for other shortened URLs
        elif not is_canonical_permalink(url):
            try:
                headers = {'User-Agent': 'ContentHub/1.0'}
                response = requests.head(url, headers=headers, allow_redirects=True)
                url = response.url
            except:
                pass  # Use original URL if redirect fails
        
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        extractor_path = script_dir / "reddit-extractor.js"
        
        # Run the Node.js extractor
        result = subprocess.run(
            ["node", str(extractor_path), url, "-"],
            capture_output=True,
            text=True,
            cwd=str(script_dir),
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            return {
                'success': False,
                'error': f'Extraction failed: {error_msg}',
                'title': 'Reddit Post',
                'url': url
            }
        
        # The extractor writes to file, but we captured stdout
        # Look for the success message in stdout
        if "✅ Reddit post saved" in result.stdout:
            # Extract title and metadata from success message
            lines = result.stdout.strip().split('\n')
            title = "Reddit Post"
            subreddit = ""
            comments_count = 0
            
            for line in lines:
                if line.startswith("Title:"):
                    title = line.replace("Title:", "").strip()
                elif line.startswith("Subreddit:"):
                    subreddit = line.replace("Subreddit:", "").strip().replace("r/", "")
                elif line.startswith("Comments:"):
                    try:
                        comments_count = int(line.replace("Comments:", "").strip())
                    except:
                        pass
            
            # Now run again to get the actual content (hacky but works)
            # Use a temp file to capture content
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as f:
                temp_file = f.name
            
            result2 = subprocess.run(
                ["node", str(extractor_path), url, temp_file],
                capture_output=True,
                text=True,
                cwd=str(script_dir),
                timeout=30
            )
            
            # Read the content
            content = ""
            try:
                with open(temp_file, 'r') as f:
                    content = f.read()
                import os
                os.unlink(temp_file)  # Clean up temp file
            except:
                pass
            
            # Extract author from content
            author = ""
            created_date = None
            if content:
                author_match = re.search(r'\*\*Posted by\*\* (u/\w+)', content)
                if author_match:
                    author = author_match.group(1)
                
                # Extract score and upvote ratio
                score = 0
                upvote_ratio = 0
                score_match = re.search(r'\*\*Score:\*\* (\d+) points \((\d+)% upvoted\)', content)
                if score_match:
                    score = int(score_match.group(1))
                    upvote_ratio = int(score_match.group(2)) / 100
                
                # Extract posted date
                date_match = re.search(r'\*\*Posted:\*\* ([^\n]+)', content)
                if date_match:
                    date_str = date_match.group(1)
                    # Parse the date and convert to ISO format
                    from datetime import datetime
                    try:
                        # Parse "9/14/2025, 12:24:44 AM" format
                        parsed_date = datetime.strptime(date_str, "%m/%d/%Y, %I:%M:%S %p")
                        created_date = parsed_date.isoformat()
                    except:
                        # Try alternative formats if needed
                        created_date = date_str
            
            return {
                'success': True,
                'title': title,
                'content': content,
                'author': author,
                'subreddit': subreddit,
                'metadata': {
                    'comments': comments_count,
                    'score': score,
                    'upvote_ratio': upvote_ratio,
                    'platform': 'reddit',
                    'created': created_date
                },
                'url': url
            }
            
        else:
            # Try to parse JSON output (if extractor was modified)
            try:
                output = result.stdout.strip()
                # Find JSON in output
                json_start = output.find('{')
                if json_start >= 0:
                    data = json.loads(output[json_start:])
                    return {
                        'success': data.get('success', True),
                        'title': data.get('title', 'Reddit Post'),
                        'content': data.get('content', ''),
                        'author': data.get('author', ''),
                        'subreddit': data.get('metadata', {}).get('subreddit', ''),
                        'metadata': data.get('metadata', {}),
                        'url': url
                    }
            except:
                pass
            
            return {
                'success': False,
                'error': 'Failed to parse extractor output',
                'title': 'Reddit Post',
                'url': url
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Extraction timed out after 30 seconds',
            'title': 'Reddit Post',
            'url': url
        }
    except FileNotFoundError:
        return {
            'success': False,
            'error': 'Node.js not installed or extractor not found',
            'title': 'Reddit Post',
            'url': url
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'title': 'Reddit Post',
            'url': url
        }

# Test if running directly
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract.py <reddit-url>")
        sys.exit(1)
    
    url = sys.argv[1]
    result = extract_reddit(url)
    
    print(json.dumps(result, indent=2))