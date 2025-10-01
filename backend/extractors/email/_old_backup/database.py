#!/usr/bin/env python3
"""
Newsletter Articles Database Manager

Purpose: Manages SQLite database for storing newsletter articles with
efficient querying, deduplication, and incremental updates.

Features:
- SQLite database with indexed columns for fast queries
- Automatic deduplication by URL
- Full-text search capabilities
- Pagination support
- Category and source filtering
- Date range queries

Usage:
    from database import ArticleDatabase
    db = ArticleDatabase()
    db.insert_article(article_data)
    articles = db.get_articles(limit=50, offset=0)
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib
import sys

# Add parent paths to import ContentDatabase
sys.path.append(str(Path(__file__).parent.parent.parent))
from database.content_db import ContentDatabase


class ArticleDatabase:
    """Manage newsletter articles in SQLite database"""
    
    def __init__(self, db_path: str = 'data/articles.db'):
        """Initialize database connection and create tables if needed"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self.create_tables()
        
    def create_tables(self):
        """Create database tables and indexes"""
        cursor = self.conn.cursor()
        
        # Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                url_hash TEXT UNIQUE NOT NULL,
                domain TEXT,
                title TEXT,
                description TEXT,
                category TEXT,
                source TEXT,
                newsletter_subject TEXT,
                newsletter_sender TEXT,
                newsletter_date TEXT,
                extracted_at TEXT,
                fetch_status TEXT,
                og_title TEXT,
                og_description TEXT,
                og_image TEXT,
                meta_keywords TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON articles(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON articles(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON articles(domain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_newsletter_date ON articles(newsletter_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_extracted_at ON articles(extracted_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_hash ON articles(url_hash)')
        
        # Full-text search table (check if exists first)
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='articles_fts'
        ''')
        if not cursor.fetchone():
            cursor.execute('''
                CREATE VIRTUAL TABLE articles_fts 
                USING fts5(title, description, content=articles, content_rowid=id)
            ''')
        
        # Stats table for tracking extractions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extraction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extracted_at TEXT,
                days_back INTEGER,
                newsletters_processed INTEGER,
                articles_found INTEGER,
                articles_added INTEGER,
                duplicates_skipped INTEGER,
                errors INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def insert_article(self, article: Dict) -> bool:
        """
        Insert an article into the database
        
        Args:
            article: Article dictionary with metadata
            
        Returns:
            True if inserted, False if duplicate
        """
        cursor = self.conn.cursor()
        
        # Generate URL hash for deduplication
        url_hash = hashlib.md5(article['url'].encode()).hexdigest()
        
        try:
            cursor.execute('''
                INSERT INTO articles (
                    url, url_hash, domain, title, description, category,
                    source, newsletter_subject, newsletter_sender, 
                    newsletter_date, extracted_at, fetch_status,
                    og_title, og_description, og_image, meta_keywords
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.get('url'),
                url_hash,
                article.get('domain'),
                article.get('title'),
                article.get('description'),
                article.get('category'),
                article.get('source'),
                article.get('newsletter_subject'),
                article.get('newsletter_sender'),
                article.get('newsletter_date'),
                article.get('extracted_at', datetime.now().isoformat()),
                article.get('fetch_status'),
                article.get('og_title'),
                article.get('og_description'),
                article.get('og_image'),
                article.get('meta_keywords')
            ))
            
            # Update FTS index
            cursor.execute('''
                INSERT INTO articles_fts(rowid, title, description)
                VALUES (last_insert_rowid(), ?, ?)
            ''', (
                article.get('title', ''),
                article.get('description', '')
            ))
            
            self.conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            # Duplicate URL
            return False
    
    def insert_batch(self, articles: List[Dict]) -> Tuple[int, int]:
        """
        Insert multiple articles in a batch
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Tuple of (articles_added, duplicates_skipped)
        """
        added = 0
        skipped = 0
        
        for article in articles:
            if self.insert_article(article):
                added += 1
            else:
                skipped += 1
        
        return added, skipped
    
    def get_articles(self, 
                    limit: int = 50,
                    offset: int = 0,
                    category: Optional[str] = None,
                    source: Optional[str] = None,
                    domain: Optional[str] = None,
                    days_back: Optional[int] = None,
                    search: Optional[str] = None) -> List[Dict]:
        """
        Query articles with filters and pagination
        
        Args:
            limit: Maximum number of articles to return
            offset: Number of articles to skip
            category: Filter by category
            source: Filter by source
            domain: Filter by domain
            days_back: Only get articles from last N days
            search: Full-text search query
            
        Returns:
            List of article dictionaries
        """
        cursor = self.conn.cursor()
        
        # Build query
        where_clauses = []
        params = []
        
        if category:
            where_clauses.append('category = ?')
            params.append(category)
        
        if source:
            where_clauses.append('source = ?')
            params.append(source)
        
        if domain:
            where_clauses.append('domain = ?')
            params.append(domain)
        
        if days_back:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            where_clauses.append('newsletter_date >= ?')
            params.append(cutoff_date)
        
        if search:
            # Use FTS for search
            query = f'''
                SELECT a.* FROM articles a
                JOIN articles_fts ON a.id = articles_fts.rowid
                WHERE articles_fts MATCH ?
                {' AND ' + ' AND '.join(where_clauses) if where_clauses else ''}
                ORDER BY datetime(a.newsletter_date) DESC
                LIMIT ? OFFSET ?
            '''
            params = [search] + params + [limit, offset]
        else:
            where_clause = ' WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''
            query = f'''
                SELECT * FROM articles
                {where_clause}
                ORDER BY datetime(newsletter_date) DESC
                LIMIT ? OFFSET ?
            '''
            params = params + [limit, offset]
        
        cursor.execute(query, params)
        
        # Convert rows to dictionaries
        articles = []
        for row in cursor.fetchall():
            articles.append(dict(row))
        
        return articles
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total articles
        cursor.execute('SELECT COUNT(*) FROM articles')
        stats['total_articles'] = cursor.fetchone()[0]
        
        # Articles by category
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM articles 
            GROUP BY category 
            ORDER BY count DESC
        ''')
        stats['by_category'] = [dict(row) for row in cursor.fetchall()]
        
        # Articles by source
        cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM articles 
            GROUP BY source 
            ORDER BY count DESC
        ''')
        stats['by_source'] = [dict(row) for row in cursor.fetchall()]
        
        # Articles by domain (top 20)
        cursor.execute('''
            SELECT domain, COUNT(*) as count 
            FROM articles 
            GROUP BY domain 
            ORDER BY count DESC 
            LIMIT 20
        ''')
        stats['top_domains'] = [dict(row) for row in cursor.fetchall()]
        
        # Date range
        cursor.execute('''
            SELECT MIN(newsletter_date) as oldest, 
                   MAX(newsletter_date) as newest 
            FROM articles
        ''')
        row = cursor.fetchone()
        stats['date_range'] = {
            'oldest': row[0],
            'newest': row[1]
        }
        
        # Recent extraction logs
        cursor.execute('''
            SELECT * FROM extraction_log 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        stats['recent_extractions'] = [dict(row) for row in cursor.fetchall()]
        
        return stats
    
    def log_extraction(self, 
                      days_back: int,
                      newsletters_processed: int,
                      articles_found: int,
                      articles_added: int,
                      duplicates_skipped: int,
                      errors: int = 0):
        """Log extraction statistics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO extraction_log (
                extracted_at, days_back, newsletters_processed,
                articles_found, articles_added, duplicates_skipped, errors
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            days_back,
            newsletters_processed,
            articles_found,
            articles_added,
            duplicates_skipped,
            errors
        ))
        self.conn.commit()
    
    def cleanup_old_articles(self, days_to_keep: int = 90):
        """Remove articles older than specified days"""
        cursor = self.conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        # Delete from FTS first
        cursor.execute('''
            DELETE FROM articles_fts 
            WHERE rowid IN (
                SELECT id FROM articles WHERE newsletter_date < ?
            )
        ''', (cutoff_date,))
        
        # Delete from main table
        cursor.execute('DELETE FROM articles WHERE newsletter_date < ?', (cutoff_date,))
        
        deleted = cursor.rowcount
        self.conn.commit()
        
        # Vacuum to reclaim space
        cursor.execute('VACUUM')
        
        return deleted
    
    def close(self):
        """Close database connection"""
        self.conn.close()