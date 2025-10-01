#!/usr/bin/env python3
"""
Newsletter Articles Frontend Server

Purpose: Serves a web interface for viewing extracted newsletter articles.
Provides API endpoints and static file serving for the frontend dashboard.

Features:
- Serves static HTML/CSS/JS files
- API endpoint for articles data
- CORS support for local development
- Auto-reload of articles on file change

Usage:
    python3 server.py
    Then open http://localhost:8080 in your browser
"""

import os
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

class ArticleServer(SimpleHTTPRequestHandler):
    """Custom HTTP server for serving frontend and API"""
    
    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        # API endpoint for articles
        if parsed_path.path == '/api/articles':
            self.serve_articles()
            return
        
        # Serve frontend files
        if parsed_path.path == '/':
            self.path = '/frontend/index.html'
        elif not parsed_path.path.startswith('/frontend/'):
            self.path = '/frontend' + parsed_path.path
        
        return super().do_GET()
    
    def serve_articles(self):
        """Serve articles JSON from output directory"""
        try:
            articles_path = Path('output/articles.json')
            
            if articles_path.exists():
                with open(articles_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            else:
                # Send empty articles if file doesn't exist
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'articles': [],
                    'metadata': {
                        'total': 0,
                        'sources': []
                    }
                }).encode())
        except Exception as e:
            self.send_error(500, f"Error loading articles: {str(e)}")

def run_server(port=8080):
    """Start the HTTP server"""
    os.chdir(Path(__file__).parent)  # Change to script directory
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, ArticleServer)
    
    print(f"""
╔════════════════════════════════════════════╗
║   📰 Newsletter Articles Dashboard          ║
║                                              ║
║   Server running at:                        ║
║   http://localhost:{port}                      ║
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