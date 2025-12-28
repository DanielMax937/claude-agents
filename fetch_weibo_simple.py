#!/usr/bin/env python3
"""
Simple Weibo Content Fetcher - Fetch Weibo posts using universal-scraper

Usage:
    python fetch_weibo_simple.py --url <WEIBO_URL>
    python fetch_weibo_simple.py --url <WEIBO_URL> --max 10
    python fetch_weibo_simple.py --url <WEIBO_URL> --save output.md
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import argparse


def fetch_weibo(url, max_posts=5, headless=False):
    """Fetch Weibo content using the universal-scraper"""
    scraper_path = Path.home() / ".claude" / "skills" / "universal-scraper"  / "scripts" / "universal-scraper.js"
    
    if not scraper_path.exists():
        print(f"Error: Universal scraper not found at {scraper_path}")
        return None
    
    # Build command
    cmd = [
        "node",
        str(scraper_path),
        "--url", url,
        "--max", str(max_posts),
        "--headless", "true" if headless else "false",
        "--format", "markdown",
        "--timeout", "60000"
    ]
    
    print(f"Fetching Weibo content from: {url}")
    print(f"Max posts: {max_posts}")
    if not headless:
        print("\nBrowser will open - login manually if needed...")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,  # 3 minutes
            cwd=scraper_path.parent.parent
        )
        
        if result.returncode == 0:
            print("✓ Successfully fetched content\n")
            return result.stdout
        else:
            print(f"✗ Scraper failed with exit code {result.returncode}")
            print(f"Error: {result.stderr or result.stdout}")
            return None
            
    except subprocess.TimeoutExpired:
        print("✗ Scraper timed out after 3 minutes")
        return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def save_to_file(content, filename=None, url=None):
    """Save content to file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weibo_{timestamp}.md"
    
    filepath = Path(filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Weibo Content\n\n")
            f.write(f"Fetched at: {datetime.now().isoformat()}\n")
            if url:
                f.write(f"URL: {url}\n")
            f.write(f"\n---\n\n")
            f.write(content)
        
        print(f"✓ Saved to {filepath}")
        return filepath
    except Exception as e:
        print(f"✗ Failed to save: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Weibo posts using universal-scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_weibo_simple.py --url https://weibo.com/u/1234567890
  python fetch_weibo_simple.py --url https://weibo.com/u/1234567890 --max 10
  python fetch_weibo_simple.py --url https://weibo.com/u/1234567890 --save
  python fetch_weibo_simple.py --url https://weibo.com/u/1234567890 --save output.md

Note:
  - Browser will open for login if not already logged in
  - Sessions are persistent (login once)
  - Use --headless to run without GUI (may fail if login needed)
        """
    )
    
    parser.add_argument(
        '--url',
        type=str,
        required=True,
        help='Weibo profile URL (e.g., https://weibo.com/u/1234567890)'
    )
    parser.add_argument(
        '--max',
        type=int,
        default=5,
        help='Maximum number of posts to fetch (default: 5)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (no GUI)'
    )
    parser.add_argument(
        '--save',
        nargs='?',
        const=True,
        help='Save to file (optionally specify filename)'
    )
    
    args = parser.parse_args()
    
    # Fetch content
    content = fetch_weibo(args.url, args.max, args.headless)
    
    if content:
        # Display content
        print("=" * 60)
        print("WEIBO CONTENT")
        print("=" * 60)
        print(content)
        print("=" * 60)
        
        # Save if requested
        if args.save:
            filename = None if args.save == True else args.save
            save_to_file(content, filename, args.url)
    else:
        print("\nFailed to fetch content.")
        sys.exit(1)


if __name__ == "__main__":
    main()
