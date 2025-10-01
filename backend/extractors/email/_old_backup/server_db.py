#!/usr/bin/env python3
"""
Newsletter Articles Database Server

Purpose: Serves a web interface for viewing extracted newsletter articles
from SQLite database with pagination and filtering support.

Features:
- Serves static HTML/CSS/JS files
- Database-backed API endpoints with pagination
- Real-time search and filtering
- Efficient query performance

Usage:
    python3 server_db.py
    Then open http://localhost:8080 in your browser
"""

import os
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
from database import ArticleDatabase

# Load paths configuration
def load_paths_config():
    config_path = Path(__file__).parent.parent / 'paths_config.json'
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return None

PATHS_CONFIG = load_paths_config()

class ArticleDatabaseServer(SimpleHTTPRequestHandler):
    """Custom HTTP server for serving frontend and database API"""
    
    def __init__(self, *args, **kwargs):
        # Use paths from config if available
        if PATHS_CONFIG:
            db_path = Path(__file__).parent.parent / PATHS_CONFIG['files']['database']
        else:
            db_path = Path(__file__).parent.parent / 'data' / 'articles.db'
        self.db = ArticleDatabase(str(db_path))
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        # API endpoints
        if parsed_path.path == '/api/articles':
            self.serve_articles_from_db(parsed_path.query)
            return
        elif parsed_path.path == '/api/stats':
            self.serve_stats()
            return
        
        # Serve frontend files
        if parsed_path.path == '/':
            self.path = '/frontend/index.html'
        elif not parsed_path.path.startswith('/api/') and not parsed_path.path.startswith('/frontend/'):
            # Add frontend prefix for static files (CSS, JS, etc)
            self.path = '/frontend' + parsed_path.path
        # If it already has /frontend/ or is an API call, leave it as is
        
        return super().do_GET()
    
    def serve_articles_from_db(self, query_string):
        """Serve articles from database with pagination and filtering"""
        try:
            # Parse query parameters
            params = urllib.parse.parse_qs(query_string)
            
            # Extract parameters with defaults
            limit = int(params.get('limit', ['50'])[0])
            offset = int(params.get('offset', ['0'])[0])
            category = params.get('category', [None])[0]
            source = params.get('source', [None])[0]
            search = params.get('search', [None])[0]
            days_back = params.get('days', [None])[0]
            
            if days_back:
                days_back = int(days_back)
            
            # Query database
            articles = self.db.get_articles(
                limit=limit,
                offset=offset,
                category=category,
                source=source,
                days_back=days_back,
                search=search
            )
            
            # Get total count for pagination
            # For simplicity, we'll include metadata
            stats = self.db.get_stats()
            
            response = {
                'articles': articles,
                'metadata': {
                    'total': stats['total_articles'],
                    'limit': limit,
                    'offset': offset,
                    'has_more': len(articles) == limit
                }
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, default=str).encode())
            
        except Exception as e:
            self.send_error(500, f"Error querying database: {str(e)}")
    
    def serve_stats(self):
        """Serve database statistics"""
        try:
            stats = self.db.get_stats()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(stats, default=str).encode())
            
        except Exception as e:
            self.send_error(500, f"Error getting stats: {str(e)}")

def run_server(port=8080):
    """Start the HTTP server"""
    # Change to project root directory, not backend
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check if database exists
    db_path = Path(__file__).parent.parent / 'data' / 'articles.db'
    if not db_path.exists():
        print(f"⚠️  Database not found at {db_path}")
        print("   Run extraction with --use-db flag first:")
        print("   python3 src/extract_articles.py --days 30 --use-db")
        return
    
    # Initialize database to show stats
    db = ArticleDatabase(str(db_path))
    stats = db.get_stats()
    db.close()
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, ArticleDatabaseServer)
    
    print(f"""
╔════════════════════════════════════════════╗
║   📰 Newsletter Articles Dashboard (DB)      ║
║                                              ║
║   Server running at:                        ║
║   http://localhost:{port}                      ║
║                                              ║
║   Database: {stats['total_articles']} articles                      ║
║   Date range: {stats['date_range']['oldest'][:10] if stats['date_range']['oldest'] else 'N/A'}    ║
║            to {stats['date_range']['newest'][:10] if stats['date_range']['newest'] else 'N/A'}    ║
║                                              ║
║   Press Ctrl+C to stop                      ║
╚════════════════════════════════════════════╝
    """)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()