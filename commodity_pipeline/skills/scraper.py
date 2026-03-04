"""Wrapper for eastmoney.com news scraping using universal-scraper (Playwright)."""
import subprocess
import json
import re
import html
from typing import List
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from commodity_pipeline.models import NewsItem


class ScraperSkill:
    """Wrapper for scraping news from eastmoney.com using universal-scraper."""

    def __init__(self):
        """Initialize with path to the universal-scraper script."""
        self._script_path = Path.home() / ".claude" / "skills" / "universal-scraper" / "scripts" / "universal-scraper.js"
        if not self._script_path.exists():
            raise FileNotFoundError(f"universal-scraper script not found: {self._script_path}")

    def get_news(self, keyword: str, sources: List[str] = None,
                 max_per_source: int = 5) -> List[NewsItem]:
        """Scrape news articles for a keyword from eastmoney.com.

        Process:
        1. Search eastmoney.com for the keyword
        2. Extract news URLs from the search results
        3. Fetch each article using universal-scraper
        4. Parse and return structured news items
        """
        # Step 1: Get search results page from eastmoney.com
        search_html = self._fetch_eastmoney_search(keyword)
        if not search_html:
            return []

        # Step 2: Parse news URLs from the HTML
        news_urls = self._parse_eastmoney_urls(search_html, max_per_source)
        if not news_urls:
            return []

        # Step 3: Fetch each article content in parallel
        news_items = self._fetch_articles_parallel(news_urls, max_workers=3)

        return news_items

    def _fetch_eastmoney_search(self, keyword: str) -> str:
        """Fetch the eastmoney.com search results page using universal-scraper.

        Uses a CSS selector to extract just the news articles section.
        """
        from urllib.parse import quote

        search_url = f"https://so.eastmoney.com/web/s?keyword={quote(keyword)}"

        # Build command as a single string for shell=True
        cmd_str = f'node "{self._script_path}" --url "{search_url}" --selector "div.searchindexarticles" --format json'

        try:
            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True,
                text=True,
                timeout=90  # Longer timeout for eastmoney.com
            )

            if result.returncode != 0:
                return ""

            # Parse JSON output
            output = result.stdout.strip()
            json_output = self._parse_json_output(output)

            if json_output:
                # If elements were found, return the structured data
                if "elements" in json_output and json_output["elements"]:
                    # The first element contains all the news text
                    return json_output["elements"][0].get("text", "")
                # Otherwise return the text content
                return json_output.get("text", "")
        except subprocess.TimeoutExpired:
            return ""
        except Exception:
            return ""

        return ""

    def _parse_json_output(self, output: str) -> dict:
        """Parse JSON from mixed stdout/stderr output."""
        # Try parsing the entire output as JSON first (handles multiline JSON)
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            pass

        # If that fails, try to find JSON object in output (handles stderr mixed in)
        # Look for lines that start with '{'
        json_start = None
        brace_count = 0
        json_chars = []

        for char in output:
            if char == '{':
                if json_start is None:
                    json_start = True
                brace_count += 1
                json_chars.append(char)
            elif char == '}':
                brace_count -= 1
                json_chars.append(char)
                if brace_count == 0 and json_start:
                    # Found complete JSON object
                    json_str = ''.join(json_chars)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        # Reset and continue looking
                        json_chars = []
                        json_start = None
                        brace_count = 0
            elif json_start:
                json_chars.append(char)

        return {}

    def _parse_eastmoney_urls(self, text: str, max_results: int) -> List[dict]:
        """Parse news items from eastmoney.com search results text.

        The text format from the page is like:
        乙二醇连续主力合约日内涨4%2025-12-24 15:03:56 - 每经AI快讯...http://futures.eastmoney.com/a/...

        Each news item is: [title][date] - [summary][url]
        Items are concatenated without clear delimiters.
        """
        news_items = []

        # Find all URLs first
        url_pattern = re.compile(r'(https?://[a-z]+\.eastmoney\.com/a/[0-9]+\.html)')
        urls = url_pattern.findall(text)

        for i, url in enumerate(urls):
            if len(news_items) >= max_results:
                break

            # Find the position of this URL
            url_pos = text.find(url)

            # Find the previous URL's position to determine our search range
            if i > 0:
                prev_url_pos = text.find(urls[i - 1])
                search_start = prev_url_pos + len(urls[i - 1])
            else:
                search_start = 0

            # Extract the text chunk for this news item
            chunk = text[search_start:url_pos + len(url)]

            # Parse the chunk to extract title, date, and summary
            # Pattern: [title][date] - [summary][url]

            # Find the date pattern (YYYY-MM-DD HH:MM:SS)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', chunk)
            if date_match:
                date_str = date_match.group(1)
                date_end_pos = date_match.end()

                # Text after the date (contains " - " and summary)
                after_date = chunk[date_end_pos:].strip()

                # Find the summary (after " - ")
                if " - " in after_date:
                    summary = after_date.split(" - ", 1)[1].strip()
                    # Remove the URL from the end of the summary
                    summary = re.sub(r'https?://[a-z]+\.eastmoney\.com/a/[0-9]+\.html$', '', summary).strip()
                else:
                    summary = after_date.strip()
                    # Remove the URL from the end
                    summary = re.sub(r'https?://[a-z]+\.eastmoney\.com/a/[0-9]+\.html$', '', summary).strip()

                # Title is before the date
                title_context = chunk[:date_match.start()].strip()

                # Clean up the title - remove any trailing non-word characters
                title = re.sub(r'[^\w\u4e00-\u9fff%]+$', '', title_context).strip()

                if title and len(title) > 3:  # Valid title
                    # Parse date
                    published = datetime.now().date()
                    try:
                        published = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
                    except ValueError:
                        pass

                    news_items.append({
                        'url': url,
                        'title': title,
                        'summary': summary,
                        'published': published,
                        'source': 'eastmoney.com'
                    })

        return news_items

    def _fetch_articles_parallel(self, news_items: List[dict], max_workers: int = 3) -> List[NewsItem]:
        """Fetch article contents in parallel using universal-scraper."""
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(self._fetch_single_article, item): item
                for item in news_items
            }

            for future in as_completed(future_to_item, timeout=180):
                item = future_to_item[future]
                try:
                    news_item = future.result()
                    if news_item:
                        results.append(news_item)
                except Exception as e:
                    # Fall back to basic item if fetch fails
                    results.append(NewsItem(
                        title=item['title'],
                        source=item['source'],
                        url=item['url'],
                        published=item['published'],
                        summary=item['summary'],
                        sentiment=None
                    ))

        return results

    def _fetch_single_article(self, item: dict) -> NewsItem:
        """Fetch a single article using universal-scraper."""
        cmd = [
            "node",
            str(self._script_path),
            "--url", item['url'],
            "--format", "json",
            "--timeout", "15000"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=25
            )

            summary = item['summary']

            # Try to parse JSON and get more detailed content
            if result.returncode == 0:
                json_output = self._parse_json_output(result.stdout.strip())
                if json_output:
                    text = json_output.get("text", "")
                    if text and len(text) > 50:
                        summary = text[:500] + "..." if len(text) > 500 else text

            return NewsItem(
                title=item['title'],
                source=item['source'],
                url=item['url'],
                published=item['published'],
                summary=summary,
                sentiment=None
            )
        except Exception:
            # Return basic item on any error
            return NewsItem(
                title=item['title'],
                source=item['source'],
                url=item['url'],
                published=item['published'],
                summary=item['summary'],
                sentiment=None
            )
