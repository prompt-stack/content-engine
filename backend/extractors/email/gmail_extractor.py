#!/usr/bin/env python3
"""
Gmail Newsletter Extractor

Purpose: Connects to Gmail via OAuth2 and extracts newsletter emails based on
configured sources and search patterns.

Key Features:
- OAuth2 authentication with token persistence
- Flexible email search with date ranges and sender filters
- HTML and text body extraction
- Batch fetching for efficiency
- Excel export capability (optional)

Usage:
    from gmail_extractor import GmailNewsletterExtractor
    extractor = GmailNewsletterExtractor()
    newsletters = extractor.search_newsletters(query='from:news@example.com')

Requires:
    - credentials.json: OAuth2 credentials from Google Cloud Console
    - Gmail API enabled in Google Cloud project
"""

import os
import base64
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from typing import List, Dict, Optional, Tuple
import re
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path


class GmailExtractor:
    """Extract and process emails from Gmail based on config"""

    # If modifying these scopes, delete the token file.
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, credentials_file='credentials.json', token_file='token.pickle', token_data: Optional[Dict] = None):
        """
        Initialize the Gmail Newsletter Extractor

        Args:
            credentials_file: Path to OAuth2 credentials JSON file (legacy)
            token_file: Path to store/retrieve authentication token (legacy)
            token_data: OAuth token data dictionary (new, per-user approach)
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.token_data = token_data
        self.service = None
        self._authenticate()
        
    def _authenticate(self):
        """Authenticate and return Gmail service instance"""
        creds = None

        # NEW: If token_data is provided, use it (per-user OAuth tokens)
        if self.token_data:
            try:
                from datetime import datetime
                expiry = None
                if self.token_data.get("expiry"):
                    expiry = datetime.fromisoformat(self.token_data["expiry"])

                creds = Credentials(
                    token=self.token_data.get("token"),
                    refresh_token=self.token_data.get("refresh_token"),
                    token_uri=self.token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                    client_id=self.token_data.get("client_id"),
                    client_secret=self.token_data.get("client_secret"),
                    scopes=self.token_data.get("scopes", self.SCOPES),
                    expiry=expiry
                )

                # Refresh if expired
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    print("🔄 Refreshed expired Google OAuth token")

                print("✅ Successfully authenticated with user's Google OAuth token")
            except Exception as e:
                raise Exception(f"Failed to authenticate with provided token data: {e}")

        # LEGACY: Fall back to token file approach
        else:
            # Token file stores the user's access and refresh tokens
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)

            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)

            print("✅ Successfully authenticated with Gmail API (legacy token file)")

        self.service = build('gmail', 'v1', credentials=creds)
    
    def get_user_profile(self) -> Dict:
        """Get the authenticated user's Gmail profile"""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile
        except Exception as error:
            print(f'Error getting profile: {error}')
            return {}
    
    def search_newsletters(self, 
                         query: str = None,
                         days_back: int = 7,
                         max_results: int = 50,
                         sender_filter: List[str] = None) -> List[Dict]:
        """
        Search for newsletters in Gmail
        
        Args:
            query: Custom Gmail search query (optional)
            days_back: Number of days to look back
            max_results: Maximum number of emails to retrieve
            sender_filter: List of sender emails/domains to filter
            
        Returns:
            List of email dictionaries
        """
        # Build search query
        if not query:
            # Default query to find common newsletter patterns
            date_after = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            query_parts = [f'after:{date_after}']
            
            # Add newsletter indicators
            newsletter_indicators = '(list:* OR unsubscribe OR "view in browser" OR "newsletter" OR "weekly digest" OR "daily brief" OR "weekly roundup")'
            query_parts.append(newsletter_indicators)
            
            # Add sender filter if provided
            if sender_filter:
                sender_query = ' OR '.join([f'from:{sender}' for sender in sender_filter])
                query_parts.append(f'({sender_query})')
            
            query = ' AND '.join(query_parts)
        
        print(f"🔍 Searching with query: {query}")
        
        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print('No newsletters found.')
                return []
            
            print(f"📧 Found {len(messages)} potential newsletters")
            
            # Fetch full message details
            newsletters = []
            for i, msg in enumerate(messages, 1):
                print(f"  Fetching {i}/{len(messages)}...", end='\r')
                newsletter = self._get_message_details(msg['id'])
                if newsletter:
                    newsletters.append(newsletter)
            
            print(f"\n✅ Successfully fetched {len(newsletters)} newsletters")
            return newsletters
            
        except Exception as error:
            print(f'❌ An error occurred: {error}')
            return []
    
    def _get_message_details(self, msg_id: str) -> Optional[Dict]:
        """
        Get full details of a message
        
        Args:
            msg_id: Gmail message ID
            
        Returns:
            Dictionary with message details or None
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            to = next((h['value'] for h in headers if h['name'] == 'To'), '')
            
            # Extract sender email
            sender_email = self._extract_email(sender)
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            return {
                'id': msg_id,
                'thread_id': message.get('threadId', ''),
                'subject': subject,
                'sender': sender,
                'sender_email': sender_email,
                'to': to,
                'date': date,
                'snippet': message.get('snippet', ''),
                'body_text': body['text'],
                'body_html': body['html'],
                'labels': message.get('labelIds', []),
                'size_estimate': message.get('sizeEstimate', 0)
            }
            
        except Exception as error:
            print(f'Error retrieving message {msg_id}: {error}')
            return None
    
    def _extract_email(self, sender_string: str) -> str:
        """Extract email address from sender string"""
        email_pattern = r'<(.+?)>'
        match = re.search(email_pattern, sender_string)
        if match:
            return match.group(1)
        # If no angle brackets, assume the whole string is the email
        return sender_string.strip()
    
    def _extract_body(self, payload: Dict) -> Dict[str, str]:
        """
        Extract text and HTML body from message payload
        
        Args:
            payload: Gmail message payload
            
        Returns:
            Dictionary with 'text' and 'html' content
        """
        body = {'text': '', 'html': ''}
        
        def extract_parts(parts):
            for part in parts:
                mimeType = part.get('mimeType', '')
                if 'parts' in part:
                    extract_parts(part['parts'])
                elif mimeType == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body['text'] += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif mimeType == 'text/html':
                    data = part['body'].get('data', '')
                    if data:
                        body['html'] += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        if 'parts' in payload:
            extract_parts(payload['parts'])
        else:
            # Single part message
            body_data = payload.get('body', {}).get('data', '')
            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                if payload.get('mimeType') == 'text/html':
                    body['html'] = decoded
                else:
                    body['text'] = decoded
        
        return body
    
    def extract_content(self, newsletter: Dict, extract_links: bool = True) -> Dict:
        """
        Extract clean content from newsletter
        
        Args:
            newsletter: Newsletter dictionary
            extract_links: Whether to extract links
            
        Returns:
            Dictionary with extracted content
        """
        content = {
            'subject': newsletter['subject'],
            'sender': newsletter['sender'],
            'sender_email': newsletter['sender_email'],
            'date': newsletter['date'],
            'text': '',
            'links': [],
            'images': []
        }
        
        # Use HTML if available, otherwise use text
        if newsletter['body_html']:
            soup = BeautifulSoup(newsletter['body_html'], 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            content['text'] = soup.get_text(separator='\n', strip=True)
            
            # Extract links if requested
            if extract_links:
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    text = link.get_text(strip=True)
                    # Filter out unsubscribe and tracking links
                    if not any(word in href.lower() for word in ['unsubscribe', 'email_open', 'email_click', 'manage-preferences', 'update-profile']):
                        links.append({'text': text, 'url': href})
                content['links'] = links
            
            # Extract images
            images = []
            for img in soup.find_all('img', src=True):
                src = img['src']
                alt = img.get('alt', '')
                if not any(word in src.lower() for word in ['tracking', 'pixel', 'spacer']):
                    images.append({'src': src, 'alt': alt})
            content['images'] = images[:10]  # Limit to first 10 images
        else:
            content['text'] = newsletter['body_text']
            
            # Extract links from plain text
            if extract_links:
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, newsletter['body_text'])
                content['links'] = [{'text': '', 'url': url} for url in urls 
                                  if not any(word in url.lower() for word in ['unsubscribe', 'email_open'])]
        
        return content
    
    def save_newsletters(self, newsletters: List[Dict], output_file: str = 'newsletters.json'):
        """
        Save newsletters to JSON file
        
        Args:
            newsletters: List of newsletter dictionaries
            output_file: Output file path
        """
        # Create output directory if it doesn't exist
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(newsletters, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Saved {len(newsletters)} newsletters to {output_path}")
    
    def create_digest(self, newsletters: List[Dict], output_file: str = 'digest.md'):
        """
        Create a markdown digest of newsletters
        
        Args:
            newsletters: List of newsletter dictionaries
            output_file: Output markdown file path
        """
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# 📰 Newsletter Digest\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Total Newsletters:** {len(newsletters)}\n\n")
            f.write("---\n\n")
            
            # Group by sender
            by_sender = {}
            for newsletter in newsletters:
                content = self.extract_content(newsletter)
                sender = content['sender_email']
                if sender not in by_sender:
                    by_sender[sender] = []
                by_sender[sender].append(content)
            
            for sender, items in by_sender.items():
                f.write(f"## 📧 From: {sender}\n\n")
                for content in items:
                    f.write(f"### {content['subject']}\n")
                    f.write(f"*{content['date']}*\n\n")
                    
                    # Write first 500 characters of content
                    text_preview = content['text'][:500] + '...' if len(content['text']) > 500 else content['text']
                    f.write(f"{text_preview}\n\n")
                    
                    # Add top 5 links
                    if content['links']:
                        f.write("**🔗 Key Links:**\n")
                        for link in content['links'][:5]:
                            if link['text']:
                                f.write(f"- [{link['text'][:50]}]({link['url']})\n")
                            else:
                                f.write(f"- <{link['url'][:70]}>\n")
                    
                    f.write("\n---\n\n")
        
        print(f"📝 Created digest at {output_path}")
    
    def export_to_excel(self, newsletters: List[Dict], output_file: str = 'newsletters.xlsx'):
        """
        Export newsletters to Excel file
        
        Args:
            newsletters: List of newsletter dictionaries
            output_file: Output Excel file path
        """
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Prepare data for DataFrame
        data = []
        for newsletter in newsletters:
            content = self.extract_content(newsletter)
            data.append({
                'Date': newsletter['date'],
                'Sender': newsletter['sender'],
                'Sender Email': content['sender_email'],
                'Subject': newsletter['subject'],
                'Preview': newsletter['snippet'][:200],
                'Links Count': len(content['links']),
                'Size (bytes)': newsletter.get('size_estimate', 0),
                'Labels': ', '.join(newsletter.get('labels', [])),
                'Message ID': newsletter['id']
            })
        
        df = pd.DataFrame(data)
        
        # Sort by date (newest first)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.sort_values('Date', ascending=False)
        
        # Save to Excel
        output_path = output_dir / output_file
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Newsletters', index=False)
            
            # Auto-adjust columns width
            worksheet = writer.sheets['Newsletters']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 50)
        
        print(f"📊 Exported to Excel at {output_path}")
    
    def get_statistics(self, newsletters: List[Dict]) -> Dict:
        """
        Get statistics about the newsletters
        
        Args:
            newsletters: List of newsletter dictionaries
            
        Returns:
            Dictionary with statistics
        """
        if not newsletters:
            return {}
        
        # Extract sender emails
        senders = {}
        for newsletter in newsletters:
            content = self.extract_content(newsletter, extract_links=False)
            sender = content['sender_email']
            if sender not in senders:
                senders[sender] = 0
            senders[sender] += 1
        
        # Sort senders by count
        top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)
        
        stats = {
            'total_newsletters': len(newsletters),
            'unique_senders': len(senders),
            'top_senders': top_senders[:10],
            'date_range': {
                'oldest': min(n['date'] for n in newsletters),
                'newest': max(n['date'] for n in newsletters)
            },
            'average_size_bytes': sum(n.get('size_estimate', 0) for n in newsletters) / len(newsletters)
        }
        
        return stats
