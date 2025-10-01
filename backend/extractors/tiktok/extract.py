#!/usr/bin/env python3
"""
TikTok Extractor Python Wrapper
Wraps the Node.js TikTok extractors for integration with Content Hub API
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Dict, Any

def extract_tiktok(url: str) -> Dict[str, Any]:
    """
    Extract TikTok content using Node.js extractor
    
    Args:
        url: TikTok video URL
        
    Returns:
        Dictionary with extraction results
    """
    try:
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        
        # Use the full extraction with comments for maximum data
        extractor_path = script_dir / "extract-full-with-comments.js"
        
        # Check if the extractor exists
        if not extractor_path.exists():
            # Try the metrics version
            extractor_path = script_dir / "extract-with-metrics.js"
            if not extractor_path.exists():
                # Fallback to basic extractor
                extractor_path = script_dir / "tiktok-extractor.js"
        
        # Run the Node.js extractor
        result = subprocess.run(
            ["node", str(extractor_path), url],
            capture_output=True,
            text=True,
            cwd=str(script_dir),
            timeout=30
        )
        
        if result.returncode != 0:
            # Check if it's a known error
            error_msg = result.stderr or result.stdout
            if "403" in error_msg or "blocked" in error_msg.lower():
                return {
                    'success': False,
                    'error': 'TikTok is blocking automated requests',
                    'title': 'TikTok Video',
                    'url': url
                }
            elif "no captions" in error_msg.lower() or "no transcript" in error_msg.lower():
                return {
                    'success': True,
                    'title': 'TikTok Video',
                    'url': url,
                    'transcript': '',
                    'description': 'Video has no captions/transcript available',
                    'metadata': {}
                }
            else:
                return {
                    'success': False,
                    'error': f'Extraction failed: {error_msg}',
                    'title': 'TikTok Video',
                    'url': url
                }
        
        # Parse the output - the extractors output different formats
        output = result.stdout.strip()
        
        # Try to parse as JSON first (newer extractors)
        try:
            data = json.loads(output)
            
            # Format for Content Hub
            # Use the title from the data if available
            title = data.get('title', '')
            
            # If title contains hashtags, clean it up
            if title and '#' in title:
                # Remove hashtags and clean up
                title_parts = title.split('#')[0].strip()
                # Take first sentence if it's reasonable length
                first_sentence = title_parts.split('.')[0].strip()
                if first_sentence and len(first_sentence) < 150:
                    title = first_sentence
                elif title_parts:
                    # Otherwise take first 80 chars
                    title = title_parts[:80].strip()
                    if len(title_parts) > 80:
                        title += '...'
            elif title and len(title) > 150:
                # For long titles without hashtags, truncate
                title = title[:80] + '...'
            
            # Fall back to transcript if no good title
            if not title or title == 'TikTok Video':
                if data.get('transcript'):
                    first_line = data['transcript'].split('\n')[0][:80]
                    title = f"TikTok: {first_line}..." if len(first_line) >= 80 else f"TikTok: {first_line}"
                elif data.get('description'):
                    desc_clean = data['description'].split('#')[0].strip()[:80]
                    title = f"TikTok: {desc_clean}"
                else:
                    title = f"TikTok by @{data.get('creator', 'unknown')}"
            
            # Extract creator - remove @ if present
            creator = data.get('creator', '')
            if creator.startswith('@'):
                creator = creator[1:]
            
            return {
                'success': True,
                'title': title,
                'description': data.get('description', ''),
                'transcript': data.get('transcript', ''),
                'author': creator,
                'metadata': {
                    'views': data.get('metadata', {}).get('views', 0),
                    'likes': data.get('metadata', {}).get('likes', 0),
                    'comments': data.get('metadata', {}).get('comments', 0),
                    'shares': data.get('metadata', {}).get('shares', 0),
                    'duration': data.get('metadata', {}).get('duration', 0),
                    'hashtags': data.get('hashtags', []),
                    'language': data.get('metadata', {}).get('language', 'en'),
                    'videoId': data.get('metadata', {}).get('videoId', ''),
                    'topComments': data.get('topComments', [])
                },
                'url': url
            }
        except json.JSONDecodeError:
            # Parse text output from extract-full-with-comments.js format
            lines = output.split('\n')
            title = 'TikTok Video'
            creator = ''
            description = ''
            transcript = ''
            views = 0
            likes = 0
            comments = 0
            shares = 0
            
            # Parse the formatted text output
            for i, line in enumerate(lines):
                if line.startswith('Title:'):
                    raw_title = line.replace('Title:', '').strip()
                    # Clean up title - remove hashtags and truncate if needed
                    if '#' in raw_title:
                        title = raw_title.split('#')[0].strip()[:80]
                    else:
                        title = raw_title[:80]
                    if len(raw_title) > 80:
                        title += '...'
                elif line.startswith('Creator:'):
                    creator = line.replace('Creator:', '').strip().replace('@', '')
                elif line.startswith('Views:'):
                    try:
                        views = int(line.replace('Views:', '').replace(',', '').strip())
                    except:
                        pass
                elif line.startswith('Likes:'):
                    try:
                        likes = int(line.replace('Likes:', '').replace(',', '').strip())
                    except:
                        pass
                elif line.startswith('Comments:'):
                    try:
                        comments = int(line.replace('Comments:', '').replace(',', '').strip())
                    except:
                        pass
                elif line.startswith('Shares:'):
                    try:
                        shares = int(line.replace('Shares:', '').replace(',', '').strip())
                    except:
                        pass
                elif '📝 Description:' in line or line.startswith('Description:'):
                    # Get description on next lines
                    for j in range(i+1, min(i+5, len(lines))):
                        if lines[j] and not lines[j].startswith('#') and not lines[j].startswith('📄'):
                            description = lines[j].strip()
                            break
                elif '💬 Transcript:' in line or '📄 Transcript:' in line or line.startswith('Transcript:'):
                    # Everything after "Transcript:" is the transcript
                    transcript = '\n'.join(lines[i+1:])
                    # Remove footer stats if present
                    if '👤 Creator Stats:' in transcript:
                        transcript = transcript.split('👤 Creator Stats:')[0].strip()
                    if '💾 Full data saved' in transcript:
                        transcript = transcript.split('💾 Full data saved')[0].strip()
                    if '💬 Top Comments:' in transcript:
                        transcript = transcript.split('💬 Top Comments:')[0].strip()
                    break
            
            # Use first line of transcript as title if generic
            if (not title or title == 'TikTok Video') and transcript:
                first_line = transcript.split('\n')[0][:100]
                title = f"TikTok: {first_line}..." if len(first_line) >= 100 else f"TikTok: {first_line}"
            
            return {
                'success': True,
                'title': title,
                'description': description,
                'transcript': transcript,
                'author': creator,
                'metadata': {
                    'views': views,
                    'likes': likes,
                    'comments': comments,
                    'shares': shares
                },
                'url': url
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Extraction timed out after 30 seconds',
            'title': 'TikTok Video',
            'url': url
        }
    except FileNotFoundError:
        return {
            'success': False,
            'error': 'Node.js not installed or extractor not found',
            'title': 'TikTok Video',
            'url': url
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'title': 'TikTok Video',
            'url': url
        }

# Test if running directly
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract.py <tiktok-url>")
        sys.exit(1)
    
    url = sys.argv[1]
    result = extract_tiktok(url)
    
    print(json.dumps(result, indent=2))