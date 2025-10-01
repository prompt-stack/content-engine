#!/usr/bin/env python3
"""
Clean duplicate articles from database
Keeps the newest version (by newsletter_date) of each duplicate title
"""

import sqlite3
from pathlib import Path

def clean_duplicates():
    """Remove duplicate articles, keeping newest version"""
    db_path = Path(__file__).parent.parent / 'data' / 'articles.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, let's see how many duplicates we have
    cursor.execute("""
        SELECT title, COUNT(*) as count 
        FROM articles 
        GROUP BY title 
        HAVING count > 1
    """)
    
    duplicates = cursor.fetchall()
    print(f"Found {len(duplicates)} titles with duplicates")
    
    total_removed = 0
    
    # For each duplicate title, keep only the newest one
    for title, count in duplicates:
        # Get all articles with this title, ordered by date (newest first)
        cursor.execute("""
            SELECT id, newsletter_date, extracted_at 
            FROM articles 
            WHERE title = ? 
            ORDER BY 
                CASE 
                    WHEN newsletter_date IS NOT NULL THEN newsletter_date 
                    ELSE extracted_at 
                END DESC
        """, (title,))
        
        articles = cursor.fetchall()
        
        # Keep the first (newest) one, delete the rest
        if len(articles) > 1:
            ids_to_delete = [str(article[0]) for article in articles[1:]]
            
            cursor.execute(f"""
                DELETE FROM articles 
                WHERE id IN ({','.join(ids_to_delete)})
            """)
            
            removed = len(ids_to_delete)
            total_removed += removed
            print(f"  - Removed {removed} duplicates of: {title[:50]}...")
    
    # Commit the changes
    conn.commit()
    
    # Check final count
    cursor.execute("SELECT COUNT(*) FROM articles")
    final_count = cursor.fetchone()[0]
    
    print(f"\n✅ Cleanup complete!")
    print(f"   Removed {total_removed} duplicate articles")
    print(f"   Final article count: {final_count}")
    
    conn.close()

if __name__ == "__main__":
    clean_duplicates()