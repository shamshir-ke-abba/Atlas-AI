"""
Atlas V3 Web Search Plugin

Deterministic web retrieval for Atlas.
Searches DuckDuckGo HTML and returns structured results.
"""

import html
import re
import socket
import urllib.parse
import urllib.request

from plugins.base import AtlasPlugin


class WebSearchPlugin(AtlasPlugin):
    name = "web_search"
    display_name = "Web Search"
    description = "Searches the web for current information."
    icon = "🌐"
    has_gui = False
    gui_id = "web_search"

    # Lower number = higher priority.
    priority = 25

    triggers = [
        "search the web",
        "web search",
        "search online",
        "search the internet",
        "look it up online",
        "look online",
        "latest",
        "current",
        "today",
        "recent",
        "news",
    ]

    SEARCH_URL = "https://html.duckduckgo.com/html/?q={}"
    TIMEOUT = 10
    MAX_RESULTS = 8

    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )

    def can_handle(self, message):
        text = str(message or "").strip().lower()
        if not text:
            return False

        explicit = (
            "search the web",
            "web search",
            "search online",
            "search the internet",
            "look it up online",
            "look online",
        )
        if any(text == p or text.startswith(p + " ") for p in explicit):
            return True

        # Current/fresh-information questions.
        patterns = (
            r"\bwhen\s+(?:is|was|will|does|did)\b",
            r"\bwhat(?:'s| is)\s+(?:the\s+)?latest\b",
            r"\bwho(?:'s| is)\s+(?:the\s+)?current\b",
            r"\bwhere\s+is\s+(?:the\s+)?current\b",
            r"\bhow\s+many\s+.*\b(?:today|currently|now)\b",
            r"\bcurrent\b",
            r"\blatest\b",
            r"\btoday\b",
            r"\bright\s+now\b",
            r"\brecent(?:ly)?\b",
            r"\bnews\b",
            r"\bthis\s+(?:year|month|week)\b",
        )
        return any(re.search(pattern, text) for pattern in patterns)

    def run(self, expression="", **kwargs):
        query = self._clean_query(expression)
        if not query:
            return "No search query provided."

        results = self.search_results(query)
        if not results:
            return f"No useful web results found for: {query}"

        return self._format_results(query, results)

    def search_results(self, query):
        query = self._clean_query(query)
        if not query:
            return []

        try:
            encoded = urllib.parse.quote_plus(query)
            url = self.SEARCH_URL.format(encoded)

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": self.USER_AGENT,
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,*/*;q=0.8"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                    "Connection": "close",
                },
            )

            with urllib.request.urlopen(request, timeout=self.TIMEOUT) as response:
                page = response.read().decode("utf-8", errors="ignore")

            return self._parse_results(page)

        except (TimeoutError, socket.timeout):
            return []
        except Exception:
            try:
                from core.logger import logger
                logger.exception("Web search failed")
            except Exception:
                pass
            return []

    @staticmethod
    def _clean_query(query):
        text = str(query or "").strip()
        prefixes = (
            "search the web for ",
            "search the web ",
            "web search for ",
            "web search ",
            "search online for ",
            "search online ",
            "search the internet for ",
            "search the internet ",
            "look it up online for ",
            "look it up online ",
            "look online for ",
            "look online ",
        )
        lowered = text.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return text[len(prefix):].strip()
        return text

    def _parse_results(self, page):
        results = []

        blocks = re.findall(
            r'<div[^>]*class=["\']result\b[^>]*>(.*?)</div>\s*</div>',
            page,
            re.DOTALL | re.IGNORECASE,
        )

        if not blocks:
            blocks = re.findall(
                r'(<a[^>]*class=["\'][^"\']*result__a[^"\']*["\'][^>]*>.*?</a>)',
                page,
                re.DOTALL | re.IGNORECASE,
            )

        for block in blocks:
            if len(results) >= self.MAX_RESULTS:
                break
            parsed = self._parse_result_block(block)
            if parsed:
                results.append(parsed)

        return results

    def _parse_result_block(self, block):
        title_match = re.search(
            r'<a[^>]*class=["\'][^"\']*result__a[^"\']*["\'][^>]*'
            r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if not title_match:
            return None

        title = self._clean_html(title_match.group(2))
        url = self._decode_url(title_match.group(1))
        if not title or not url:
            return None

        snippet_match = re.search(
            r'class=["\'][^"\']*result__snippet[^"\']*["\'][^>]*>(.*?)</',
            block,
            re.DOTALL | re.IGNORECASE,
        )
        snippet = (
            self._clean_html(snippet_match.group(1))
            if snippet_match
            else ""
        )

        return {
            "title": title,
            "url": url,
            "snippet": snippet,
        }

    def _format_results(self, query, results):
        lines = [f"Web results for: {query}", ""]
        for index, result in enumerate(results, 1):
            lines.append(f"{index}. {result['title']}")
            if result.get("snippet"):
                lines.append(f"   {result['snippet']}")
            lines.append(f"   {result['url']}")
            lines.append("")
        return "\n".join(lines).strip()

    @staticmethod
    def _decode_url(url):
        url = html.unescape(url or "")
        if "uddg=" in url:
            try:
                parsed = urllib.parse.urlparse(
                    "https:" + url if url.startswith("//") else url
                )
                params = urllib.parse.parse_qs(parsed.query)
                if params.get("uddg"):
                    return params["uddg"][0]
            except Exception:
                pass
        return url

    @staticmethod
    def _clean_html(text):
        text = html.unescape(text or "")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
