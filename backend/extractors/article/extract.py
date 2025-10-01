#!/usr/bin/env python3
"""
Article Extractor for Content Hub

Wrapper for Node.js article extractor that fetches and extracts clean content from any web article.
"""

import subprocess
import json
from typing import Dict, Any
from pathlib import Path

def extract_article(url: str) -> Dict[str, Any]:
    """
    Extract article content from URL
    
    Args:
        url: Web article URL to extract
        
    Returns:
        Dictionary with extraction results
    """
    try:
        # Get the directory of this script
        current_dir = Path(__file__).parent
        
        # Run the Node.js article extractor
        result = subprocess.run(
            ['node', 'article-extractor.js', url],
            cwd=current_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return {
                'success': False,
                'error': f'Extraction failed: {error_msg}'
            }
        
        # Parse the JSON output
        try:
            data = json.loads(result.stdout)
            return data
        except json.JSONDecodeError:
            # If not JSON, return the raw output
            return {
                'success': True,
                'content': result.stdout.strip(),
                'title': 'Article',
                'metadata': {}
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Extraction timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# For testing
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        # Default test URL
        test_url = 'https://techcrunch.com/'
    
    print(f"Extracting article from: {test_url}")
    result = extract_article(test_url)
    print(json.dumps(result, indent=2))