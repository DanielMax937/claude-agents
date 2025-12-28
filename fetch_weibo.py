"""
Weibo Content Fetcher - Fetch 宝树's latest Weibo posts

This script uses the skill_wrapper to call the universal-scraper skill
to fetch 宝树's latest Weibo content.
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from message_formatter import Colors


class WeiboFetcher:
    """Fetch Weibo content using the universal-scraper skill"""

    def __init__(self, use_colors=True):
        self.use_colors = use_colors
        self.c = Colors() if use_colors else type('obj', (object,), {k: '' for k in dir(Colors) if not k.startswith('_')})()
        self.scraper_path = Path.home() / ".claude" / "skills" / "universal-scraper" / "scripts" / "universal-scraper.js"

        if not self.scraper_path.exists():
            raise FileNotFoundError(f"Universal scraper not found at {self.scraper_path}")

    def fetch_baoshu_weibo(self, max_posts=5, headless=False):
        """
        Fetch 宝树's latest Weibo posts

        Args:
            max_posts: Number of posts to fetch (default: 5)
            headless: Run browser in headless mode (default: False for login)

        Returns:
            dict with success status and data/error
        """
        print(self.c.BOLD + self.c.CYAN + "📱 Fetching 宝树's Weibo Posts" + self.c.RESET)
        print(self.c.DIM + f"Max posts: {max_posts}" + self.c.RESET)
        print(self.c.DIM + f"Headless mode: {headless}" + self.c.RESET)
        print()

        # 宝树's Weibo URL (you may need to find the exact profile URL)
        # This is a placeholder - you'll need to provide the actual Weibo profile URL
        weibo_url = "https://weibo.com/u/USERID"  # Replace with actual URL

        # Build command
        cmd = [
            "node",
            str(self.scraper_path),
            "--url", weibo_url,
            "--max", str(max_posts),
            "--headless", "true" if headless else "false",
            "--format", "markdown"
        ]

        print(self.c.DIM + f"Running command: {' '.join(cmd)}" + self.c.RESET)
        print()

        try:
            # Execute scraper
            print(self.c.YELLOW + "⏳ Launching browser..." + self.c.RESET)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes timeout
                cwd=self.scraper_path.parent.parent
            )

            if result.returncode == 0:
                print(self.c.GREEN + "✓ Successfully fetched content\n" + self.c.RESET)

                return {
                    "success": True,
                    "data": result.stdout,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(self.c.RED + f"✗ Scraper failed with exit code {result.returncode}\n" + self.c.RESET)
                return {
                    "success": False,
                    "error": result.stderr or result.stdout,
                    "returncode": result.returncode
                }

        except subprocess.TimeoutExpired:
            error_msg = "Scraper timed out after 2 minutes"
            print(self.c.RED + f"✗ {error_msg}\n" + self.c.RESET)
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(self.c.RED + f"✗ {error_msg}\n" + self.c.RESET)
            return {
                "success": False,
                "error": error_msg
            }

    def fetch_weibo_by_url(self, url, max_posts=5, headless=False):
        """
        Fetch Weibo posts from any profile URL

        Args:
            url: Weibo profile URL
            max_posts: Number of posts to fetch
            headless: Run in headless mode

        Returns:
            dict with success status and data/error
        """
        print(self.c.BOLD + self.c.CYAN("📱 Fetching Weibo Posts"))
        print(self.c.DIM(f"URL: {url}"))
        print(self.c.DIM(f"Max posts: {max_posts}"))
        print()

        # Build command
        cmd = [
            "node",
            str(self.scraper_path),
            "--url", url,
            "--max", str(max_posts),
            "--headless", "true" if headless else "false",
            "--format", "markdown",
            "--timeout", "60000"
        ]

        try:
            print(self.c.YELLOW("⏳ Launching browser..."))
            if not headless:
                print(self.c.YELLOW("   Browser will open for manual login if needed"))
                print(self.c.DIM("   Login manually, then the scraper will continue automatically\n"))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,  # 3 minutes timeout
                cwd=self.scraper_path.parent.parent
            )

            if result.returncode == 0:
                print(self.c.GREEN("✓ Successfully fetched content\n"))

                return {
                    "success": True,
                    "data": result.stdout,
                    "url": url,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(self.c.RED(f"✗ Scraper failed\n"))
                print(self.c.DIM("Error details:"))
                print(result.stderr or result.stdout)
                print()

                return {
                    "success": False,
                    "error": result.stderr or result.stdout,
                    "returncode": result.returncode
                }

        except subprocess.TimeoutExpired:
            error_msg = "Scraper timed out after 3 minutes"
            print(self.c.RED(f"✗ {error_msg}\n"))
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(self.c.RED(f"✗ {error_msg}\n"))
            return {
                "success": False,
                "error": error_msg
            }

    def display_results(self, result):
        """Display fetched results in a formatted way"""
        if not result["success"]:
            print(self.c.RED("Failed to fetch content"))
            print(self.c.DIM(f"Error: {result.get('error', 'Unknown error')}"))
            return

        print(self.c.BOLD + self.c.CYAN("=" * 60))
        print(self.c.BOLD + self.c.CYAN("📱 Weibo Content"))
        print(self.c.BOLD + self.c.CYAN("=" * 60))
        print()

        # Display the content
        content = result["data"]
        print(self.c.RESET(content))

        print()
        print(self.c.DIM("-" * 60))
        print(self.c.DIM(f"Fetched at: {result['timestamp']}"))
        print(self.c.DIM("-" * 60))

    def save_to_file(self, result, filename=None):
        """Save fetched content to a file"""
        if not result["success"]:
            print(self.c.RED("Cannot save failed result"))
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"weibo_content_{timestamp}.md"

        filepath = Path(filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Weibo Content\n\n")
                f.write(f"Fetched at: {result['timestamp']}\n")
                if 'url' in result:
                    f.write(f"URL: {result['url']}\n")
                f.write(f"\n---\n\n")
                f.write(result["data"])

            print(self.c.GREEN(f"✓ Saved to {filepath}"))

        except Exception as e:
            print(self.c.RED(f"✗ Failed to save: {str(e)}"))


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch 宝树's latest Weibo posts using universal-scraper"
    )
    parser.add_argument(
        '--url',
        type=str,
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
        help='Run browser in headless mode (no GUI, may fail on login-required sites)'
    )
    parser.add_argument(
        '--save',
        type=str,
        help='Save output to file (specify filename, or auto-generate if not provided)'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    args = parser.parse_args()

    # Create fetcher
    fetcher = WeiboFetcher(use_colors=not args.no_color)

    # Check if URL provided
    if not args.url:
        print(fetcher.formatter.colors.error("Error: Please provide a Weibo profile URL"))
        print()
        print(fetcher.formatter.colors.text("Example:"))
        print(fetcher.formatter.colors.dim("  python fetch_weibo.py --url https://weibo.com/u/1234567890"))
        print(fetcher.formatter.colors.dim("  python fetch_weibo.py --url https://weibo.com/u/1234567890 --max 10"))
        print(fetcher.formatter.colors.dim("  python fetch_weibo.py --url https://weibo.com/u/1234567890 --save output.md"))
        print()
        print(fetcher.formatter.colors.yellow("Note: The browser will open for manual login if not already logged in"))
        print(fetcher.formatter.colors.yellow("      Sessions are persistent, so you only need to login once"))
        return

    # Fetch content
    result = fetcher.fetch_weibo_by_url(
        url=args.url,
        max_posts=args.max,
        headless=args.headless
    )

    # Display results
    fetcher.display_results(result)

    # Save if requested
    if args.save and result["success"]:
        fetcher.save_to_file(result, args.save if args.save != True else None)


if __name__ == "__main__":
    main()
