#!/usr/bin/env python3
"""
Create a clean, date-organized digest of all article links
Groups links by date received and shows clear metadata
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import argparse


def parse_date(date_string):
    """Parse various date formats"""
    try:
        # Try parsing the newsletter date format
        return datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
    except:
        try:
            return datetime.strptime(date_string.split(' +')[0], "%a, %d %b %Y %H:%M:%S")
        except:
            return datetime.now()


def create_date_organized_digest(input_file='output/articles.json', output_file='output/links_by_date.md'):
    """Create a clean markdown digest organized by date"""
    
    # Load the extracted articles
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Organize articles by date
    articles_by_date = defaultdict(list)
    
    for newsletter_data in data:
        newsletter = newsletter_data['newsletter']
        date = parse_date(newsletter['date'])
        date_key = date.strftime('%Y-%m-%d')
        
        for article in newsletter_data['articles']:
            if article['fetch_status'] == 'success':
                articles_by_date[date_key].append({
                    'title': article.get('og_title') or article.get('title', 'Untitled'),
                    'url': article['url'],
                    'domain': article['domain'],
                    'category': article.get('category', 'General'),
                    'description': article.get('description', ''),
                    'newsletter': newsletter['subject'][:60],
                    'time': date.strftime('%H:%M'),
                    'full_date': date.strftime('%B %d, %Y')
                })
    
    # Write the digest
    with open(output_file, 'w') as f:
        f.write("# 📅 Newsletter Links by Date\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Total Days:** {len(articles_by_date)}\n")
        f.write(f"**Total Articles:** {sum(len(articles) for articles in articles_by_date.values())}\n\n")
        f.write("---\n\n")
        
        # Sort dates in reverse chronological order
        for date_key in sorted(articles_by_date.keys(), reverse=True):
            articles = articles_by_date[date_key]
            
            # Parse date for nice formatting
            date_obj = datetime.strptime(date_key, '%Y-%m-%d')
            nice_date = date_obj.strftime('%A, %B %d, %Y')
            
            f.write(f"## 📆 {nice_date}\n\n")
            f.write(f"**Articles received:** {len(articles)}\n\n")
            
            # Group by category
            by_category = defaultdict(list)
            for article in articles:
                by_category[article['category']].append(article)
            
            # Write articles by category
            for category in ['AI/ML', 'Business', 'Technology', 'General']:
                if category in by_category:
                    f.write(f"### {category}\n\n")
                    
                    for article in by_category[category]:
                        f.write(f"**[{article['title'][:80]}]({article['url']})**\n")
                        f.write(f"- Source: {article['domain']}\n")
                        f.write(f"- From: {article['newsletter']}... ({article['time']})\n")
                        if article['description']:
                            f.write(f"- {article['description'][:150]}...\n")
                        f.write("\n")
            
            f.write("---\n\n")
    
    print(f"✅ Created date-organized digest: {output_file}")
    return output_file


def create_simple_link_list(input_file='output/articles.json', output_file='output/links_simple.md'):
    """Create a simple chronological list of all links"""
    
    # Load the extracted articles
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Collect all articles with dates
    all_articles = []
    
    for newsletter_data in data:
        newsletter = newsletter_data['newsletter']
        date = parse_date(newsletter['date'])
        
        for article in newsletter_data['articles']:
            if article['fetch_status'] == 'success' and article.get('title'):
                all_articles.append({
                    'date': date,
                    'title': article.get('og_title') or article.get('title', 'Untitled'),
                    'url': article['url'],
                    'domain': article['domain'],
                    'category': article.get('category', 'General')
                })
    
    # Sort by date (newest first)
    all_articles.sort(key=lambda x: x['date'], reverse=True)
    
    # Write simple list
    with open(output_file, 'w') as f:
        f.write("# 🔗 All Article Links (Chronological)\n\n")
        f.write(f"**Total Links:** {len(all_articles)}\n")
        f.write(f"**Period:** {all_articles[-1]['date'].strftime('%Y-%m-%d')} to {all_articles[0]['date'].strftime('%Y-%m-%d')}\n\n")
        f.write("---\n\n")
        
        current_date = None
        for article in all_articles:
            article_date = article['date'].strftime('%Y-%m-%d')
            
            # Add date header when date changes
            if article_date != current_date:
                f.write(f"\n### {article['date'].strftime('%B %d, %Y')}\n\n")
                current_date = article_date
            
            # Write link
            f.write(f"- **[{article['title'][:70]}...]({article['url']})**\n")
            f.write(f"  `{article['domain']}` | {article['category']} | {article['date'].strftime('%H:%M')}\n\n")
    
    print(f"✅ Created simple link list: {output_file}")
    return output_file


def create_csv_export(input_file='output/articles.json', output_file='output/links.csv'):
    """Export links to CSV for spreadsheet use"""
    import csv
    
    # Load the extracted articles
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Prepare CSV data
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Time', 'Title', 'URL', 'Domain', 'Category', 'Newsletter Source'])
        
        for newsletter_data in data:
            newsletter = newsletter_data['newsletter']
            date = parse_date(newsletter['date'])
            
            for article in newsletter_data['articles']:
                if article['fetch_status'] == 'success':
                    writer.writerow([
                        date.strftime('%Y-%m-%d'),
                        date.strftime('%H:%M'),
                        article.get('title', 'Untitled')[:100],
                        article['url'],
                        article['domain'],
                        article.get('category', 'General'),
                        newsletter['subject'][:60]
                    ])
    
    print(f"✅ Created CSV export: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(description='Create organized link digests')
    parser.add_argument('--input', default='output/articles.json', help='Input JSON file')
    parser.add_argument('--format', choices=['date', 'simple', 'csv', 'all'], default='all',
                       help='Output format (default: all)')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    Path('output').mkdir(exist_ok=True)
    
    if args.format in ['date', 'all']:
        create_date_organized_digest(args.input)
    
    if args.format in ['simple', 'all']:
        create_simple_link_list(args.input)
    
    if args.format in ['csv', 'all']:
        create_csv_export(args.input)
    
    if args.format == 'all':
        print("\n📚 Created all digest formats:")
        print("  • output/links_by_date.md - Organized by date with categories")
        print("  • output/links_simple.md - Simple chronological list")
        print("  • output/links.csv - Spreadsheet format")


if __name__ == "__main__":
    main()