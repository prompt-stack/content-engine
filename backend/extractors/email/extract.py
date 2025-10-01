#!/usr/bin/env python3
"""
Email Newsletter Extractor for Content Hub

Wrapper that integrates email extraction with the unified content database.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from database.content_db import ContentDatabase

def extract_emails(days_back: int = 7, source: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract emails from Gmail and save to content database
    
    Args:
        days_back: Number of days to look back for newsletters
        source: Optional specific newsletter source to extract
        
    Returns:
        Dictionary with extraction results
    """
    try:
        # Import the gmail extractor
        from gmail_extractor import GmailExtractor
        
        # Initialize extractor
        extractor = GmailExtractor()
        
        # Search for emails based on config
        emails = extractor.search_newsletters(days_back=days_back)
        
        # Initialize content database
        db = ContentDatabase()
        
        # Process and save emails
        saved_count = 0
        skipped_count = 0
        errors = []
        
        for email in emails:
            try:
                # Convert email date to ISO format
                from email.utils import parsedate_to_datetime
                date_str = email.get('date')
                published_date = None
                if date_str:
                    try:
                        # Parse email date format to datetime then to ISO
                        dt = parsedate_to_datetime(date_str)
                        published_date = dt.isoformat()
                    except:
                        # If parsing fails, use the original date
                        published_date = date_str
                
                # Prepare content for database
                content_item = {
                    'url': f"email://{email.get('id', 'unknown')}",  # Create unique URL
                    'title': email.get('subject', 'Untitled'),
                    'description': email.get('snippet', ''),
                    'content': email.get('body', ''),
                    'source_type': 'email',
                    'source': email.get('from', '').split('<')[0].strip(),  # Extract sender name
                    'author': email.get('from', ''),
                    'published_date': published_date,
                    'metadata': {
                        'email_id': email.get('id'),
                        'labels': email.get('labels', []),
                        'thread_id': email.get('thread_id')
                    }
                }
                
                # Save to database
                if db.insert_content(content_item):
                    saved_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                errors.append(f"Error processing email {email.get('id')}: {str(e)}")
        
        return {
            'success': True,
            'saved': saved_count,
            'skipped': skipped_count,
            'total': len(emails),
            'errors': errors if errors else None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'saved': 0,
            'skipped': 0,
            'total': 0
        }

# For testing
if __name__ == '__main__':
    import json
    result = extract_emails(days_back=7)
    print(json.dumps(result, indent=2))