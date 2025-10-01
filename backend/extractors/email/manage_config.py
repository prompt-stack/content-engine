#!/usr/bin/env python3
"""
Add new newsletters to your configuration
Interactive tool to add newsletter sources to config.json
"""

import json
import os
from pathlib import Path


def load_config(config_file='config.json'):
    """Load existing configuration"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Creating new configuration file: {config_file}")
        return {
            "newsletters": {
                "enabled": True,
                "sources": [],
                "additional_sources": []
            },
            "settings": {
                "default_days_back": 7,
                "max_results": 100,
                "auto_digest": True,
                "auto_excel": False,
                "output_format": ["json", "markdown"],
                "filter_promotional": True,
                "extract_links": True
            }
        }


def save_config(config, config_file='config.json'):
    """Save configuration to file"""
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ Configuration saved to {config_file}")


def add_newsletter():
    """Interactive prompt to add a newsletter"""
    print("\n📧 Add New Newsletter Source")
    print("-" * 40)
    
    # Get newsletter details
    name = input("Newsletter name (e.g., 'Morning Brew'): ").strip()
    if not name:
        print("❌ Name is required")
        return None
    
    email = input("Email address or domain (e.g., 'news@example.com' or 'example.com'): ").strip()
    if not email:
        print("❌ Email is required")
        return None
    
    # Category selection
    print("\nCategories: tech, ai, business, product, crypto, news, other")
    category = input("Category (default: 'other'): ").strip().lower() or "other"
    
    # Priority selection
    print("\nPriority: high, medium, low")
    priority = input("Priority (default: 'medium'): ").strip().lower() or "medium"
    
    # Enabled by default
    enabled_input = input("Enable this source? (Y/n): ").strip().lower()
    enabled = enabled_input != 'n'
    
    # Optional note
    note = input("Note (optional): ").strip()
    
    # Create source entry
    source = {
        "name": name,
        "email": email,
        "enabled": enabled,
        "category": category,
        "priority": priority
    }
    
    if note:
        source["note"] = note
    
    return source


def list_sources(config):
    """List all configured sources"""
    print("\n📋 Current Newsletter Sources")
    print("=" * 60)
    
    sources = config['newsletters'].get('sources', [])
    additional = config['newsletters'].get('additional_sources', [])
    
    all_sources = sources + additional
    
    if not all_sources:
        print("No sources configured yet.")
        return
    
    print(f"{'#':<3} {'Name':<25} {'Email':<30} {'Status':<8}")
    print("-" * 66)
    
    for i, source in enumerate(all_sources, 1):
        status = "✅ Active" if source.get('enabled', True) else "⏸️  Disabled"
        name = source['name'][:24]
        email = source['email'][:29]
        print(f"{i:<3} {name:<25} {email:<30} {status}")
    
    print(f"\nTotal: {len(all_sources)} sources ({len([s for s in all_sources if s.get('enabled', True)])} active)")


def toggle_source(config):
    """Enable/disable a source"""
    list_sources(config)
    
    if not config['newsletters'].get('sources'):
        return
    
    print("\nEnter source number to toggle (or 0 to cancel):")
    try:
        num = int(input("> "))
        if num == 0:
            return
        
        all_sources = config['newsletters'].get('sources', []) + config['newsletters'].get('additional_sources', [])
        
        if 1 <= num <= len(all_sources):
            source = all_sources[num - 1]
            source['enabled'] = not source.get('enabled', True)
            status = "enabled" if source['enabled'] else "disabled"
            print(f"✅ {source['name']} has been {status}")
            return True
    except (ValueError, IndexError):
        print("❌ Invalid selection")
    
    return False


def remove_source(config):
    """Remove a source from configuration"""
    list_sources(config)
    
    all_sources = config['newsletters'].get('sources', []) + config['newsletters'].get('additional_sources', [])
    
    if not all_sources:
        return
    
    print("\nEnter source number to remove (or 0 to cancel):")
    try:
        num = int(input("> "))
        if num == 0:
            return
        
        if 1 <= num <= len(all_sources):
            # Find which list it's in
            sources = config['newsletters'].get('sources', [])
            additional = config['newsletters'].get('additional_sources', [])
            
            if num <= len(sources):
                removed = sources.pop(num - 1)
            else:
                removed = additional.pop(num - len(sources) - 1)
            
            print(f"✅ Removed: {removed['name']}")
            return True
    except (ValueError, IndexError):
        print("❌ Invalid selection")
    
    return False


def main():
    """Main menu"""
    config_file = 'config.json'
    config = load_config(config_file)
    
    print("=" * 60)
    print("📧 Newsletter Configuration Manager")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. List newsletter sources")
        print("2. Add new newsletter")
        print("3. Enable/Disable source")
        print("4. Remove source")
        print("5. Save and exit")
        print("6. Exit without saving")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            list_sources(config)
        
        elif choice == '2':
            source = add_newsletter()
            if source:
                # Add to primary sources
                if 'sources' not in config['newsletters']:
                    config['newsletters']['sources'] = []
                config['newsletters']['sources'].append(source)
                print(f"✅ Added: {source['name']}")
        
        elif choice == '3':
            if toggle_source(config):
                print("Configuration updated (not saved yet)")
        
        elif choice == '4':
            if remove_source(config):
                print("Configuration updated (not saved yet)")
        
        elif choice == '5':
            save_config(config, config_file)
            print("Goodbye! 👋")
            break
        
        elif choice == '6':
            print("Exiting without saving...")
            break
        
        else:
            print("Invalid option, please try again")


if __name__ == "__main__":
    main()
