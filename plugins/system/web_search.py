"""
Atlas V3 Web Search Plugin

Fast lightweight web search for Atlas.

Design goals:
- No LLM required for searching
- Short network timeout
- Fast DuckDuckGo HTML search
- Clean result extraction
- Returns structured, useful search results
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

    description = (
        "Searches the web for current information."
    )

    icon = "🌐"

    has_gui = False

    gui_id = "web_search"

    triggers = [
        "search the web",
        "web search",
        "search online",
        "search the internet",
        "look it up online",
        "look online",
    ]

    # =========================================================
    # CONFIGURATION
    # =========================================================

    SEARCH_URL = (
        "https://html.duckduckgo.com/html/?q={}"
    )

    TIMEOUT = 3

    MAX_RESULTS = 5

    USER_AGENT = (
        "Mozilla/5.0 "
        "(X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )

    # =========================================================
    # CAN HANDLE
    # =========================================================

    def can_handle(
        self,
        message,
    ):

        text = (
            str(message)
            .lower()
            .strip()
        )

        for trigger in self.triggers:

            if text == trigger:

                return True

            if text.startswith(
                trigger + " "
            ):

                return True

        return False

    # =========================================================
    # RUN
    # =========================================================

    def run(
        self,
        expression="",
        **kwargs,
    ):

        query = (
            str(expression)
            .strip()
        )

        if not query:

            return (
                "No search query provided."
            )

        # -----------------------------------------------------
        # Remove common trigger text if the brain/plugin
        # supplied the complete user message.
        # -----------------------------------------------------

        query = self._clean_query(
            query
        )

        if not query:

            return (
                "No search query provided."
            )

        try:

            from core.logger import logger

            logger.info(
                "Web search query: %s",
                query,
            )

        except Exception:

            pass

        try:

            encoded_query = (
                urllib.parse.quote_plus(
                    query
                )
            )

            url = (
                self.SEARCH_URL.format(
                    encoded_query
                )
            )

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent":
                        self.USER_AGENT,
                    "Accept":
                        "text/html,"
                        "application/xhtml+xml,"
                        "application/xml;q=0.9,"
                        "*/*;q=0.8",
                    "Accept-Language":
                        "en-US,en;q=0.9",
                    "Connection":
                        "close",
                },
            )

            # -------------------------------------------------
            # Network request
            # -------------------------------------------------

            with urllib.request.urlopen(
                request,
                timeout=self.TIMEOUT,
            ) as response:

                page = response.read().decode(
                    "utf-8",
                    errors="ignore",
                )

            results = self._parse_results(
                page
            )

            if not results:

                return (
                    "No useful web results found "
                    f"for: {query}"
                )

            return self._format_results(
                query,
                results,
            )

        except (
            TimeoutError,
            socket.timeout,
        ):

            return (
                "Web search timed out."
            )

        except Exception as exc:

            try:

                from core.logger import logger

                logger.exception(
                    "Web search failed"
                )

            except Exception:

                pass

            return (
                "Web search failed: "
                f"{exc}"
            )

    # =========================================================
    # QUERY CLEANING
    # =========================================================

    @staticmethod
    def _clean_query(
        query,
    ):

        text = (
            str(query)
            .strip()
        )

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

            if lowered.startswith(
                prefix
            ):

                return text[
                    len(prefix):
                ].strip()

        return text

    # =========================================================
    # PARSE RESULTS
    # =========================================================

    def _parse_results(
        self,
        page,
    ):

        results = []

        # -----------------------------------------------------
        # DuckDuckGo result blocks
        # -----------------------------------------------------

        blocks = re.findall(
            r'<div[^>]*class=["\']result\b[^>]*>'
            r'(.*?)'
            r'</div>\s*</div>',
            page,
            re.DOTALL | re.IGNORECASE,
        )

        # -----------------------------------------------------
        # Fallback: locate result links directly.
        # -----------------------------------------------------

        if not blocks:

            blocks = re.findall(
                r'(<a[^>]*class=["\'][^"\']*result__a'
                r'[^"\']*["\'][^>]*>.*?</a>)',
                page,
                re.DOTALL | re.IGNORECASE,
            )

        for block in blocks:

            if len(results) >= self.MAX_RESULTS:

                break

            result = self._parse_result_block(
                block
            )

            if result is not None:

                results.append(
                    result
                )

        return results

    # =========================================================
    # PARSE RESULT BLOCK
    # =========================================================

    def _parse_result_block(
        self,
        block,
    ):

        # -----------------------------------------------------
        # Title + URL
        # -----------------------------------------------------

        title_match = re.search(
            r'<a[^>]*class=["\'][^"\']*result__a'
            r'[^"\']*["\'][^>]*href=["\']'
            r'([^"\']+)'
            r'["\'][^>]*>'
            r'(.*?)'
            r'</a>',
            block,
            re.DOTALL | re.IGNORECASE,
        )

        if not title_match:

            return None

        raw_url = html.unescape(
            title_match.group(1)
        )

        title = self._clean_html(
            title_match.group(2)
        )

        if not title:

            return None

        url = self._decode_url(
            raw_url
        )

        # -----------------------------------------------------
        # Snippet
        # -----------------------------------------------------

        snippet_match = re.search(
            r'class=["\'][^"\']*result__snippet'
            r'[^"\']*["\'][^>]*>'
            r'(.*?)'
            r'</',
            block,
            re.DOTALL | re.IGNORECASE,
        )

        if snippet_match:

            snippet = self._clean_html(
                snippet_match.group(1)
            )

        else:

            snippet = ""

        return {
            "title": title,
            "url": url,
            "snippet": snippet,
        }

    # =========================================================
    # FORMAT RESULTS
    # =========================================================

    def _format_results(
        self,
        query,
        results,
    ):

        output = [
            f"Web results for: {query}"
        ]

        output.append("")

        for index, result in enumerate(
            results,
            start=1,
        ):

            title = result.get(
                "title",
                "Untitled",
            )

            url = result.get(
                "url",
                "",
            )

            snippet = result.get(
                "snippet",
                "",
            )

            output.append(
                f"{index}. {title}"
            )

            if snippet:

                output.append(
                    f"   {snippet}"
                )

            if url:

                output.append(
                    f"   {url}"
                )

            output.append("")

        return "\n".join(
            output
        ).strip()

    # =========================================================
    # DECODE URL
    # =========================================================

    @staticmethod
    def _decode_url(
        url,
    ):

        if not url:

            return ""

        url = html.unescape(
            url
        )

        # -----------------------------------------------------
        # DuckDuckGo redirect
        # -----------------------------------------------------

        if "uddg=" in url:

            try:

                parsed = urllib.parse.urlparse(
                    (
                        "https:" + url
                        if url.startswith("//")
                        else url
                    )
                )

                params = (
                    urllib.parse.parse_qs(
                        parsed.query
                    )
                )

                if "uddg" in params:

                    return params[
                        "uddg"
                    ][0]

            except Exception:

                pass

        return url

    # =========================================================
    # CLEAN HTML
    # =========================================================

    @staticmethod
    def _clean_html(
        text,
    ):

        if not text:

            return ""

        text = html.unescape(
            text
        )

        # Remove HTML tags.
        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        # Remove excessive whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()