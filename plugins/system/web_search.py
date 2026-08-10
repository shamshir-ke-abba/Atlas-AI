"""
Atlas V3 Web Search Plugin

Lightweight web search for Atlas.
"""

import html
import re
import urllib.parse
import urllib.request
import socket

from plugins.base import AtlasPlugin


class WebSearchPlugin(AtlasPlugin):

    name = "web_search"

    description = (
        "Searches the web for current information."
    )

    triggers = [
        "search the web",
        "web search",
        "search online",
    ]

    # ==================================================
    # Plugin Matching
    # ==================================================

    def can_handle(
        self,
        message,
    ):

        text = message.lower().strip()

        for trigger in self.triggers:

            if text == trigger:
                return True

            if text.startswith(
                trigger + " "
            ):
                return True

        return False

    # ==================================================
    # Search
    # ==================================================

    def run(
        self,
        expression="",
        **kwargs,
    ):

        query = expression.strip()

        if not query:
            return "No search query provided."

        try:

            encoded_query = (
                urllib.parse.quote_plus(
                    query
                )
            )

            url = (
                "https://html.duckduckgo.com/html/?q="
                + encoded_query
            )

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent":
                        "Mozilla/5.0 "
                        "(X11; Linux x86_64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/151.0 Safari/537.36"
                },
            )

            # ------------------------------------------
            # Network timeout
            # ------------------------------------------

            with urllib.request.urlopen(
                request,
                timeout=5,
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
                    "No useful web results found."
                )

            output = []

            for index, result in enumerate(
                results[:5],
                start=1,
            ):

                output.append(
                    f"{index}. {result['title']}\n"
                    f"   {result['snippet']}\n"
                    f"   {result['url']}"
                )

            return "\n\n".join(output)

        except (
            TimeoutError,
            socket.timeout,
        ):

            return (
                "Web search timed out."
            )

        except Exception as error:

            return (
                "Web search failed: "
                + str(error)
            )

    # ==================================================
    # Parse Results
    # ==================================================

    def _parse_results(
        self,
        page,
    ):

        results = []

        blocks = re.findall(
            r'<div[^>]+class="result[^"]*"'
            r'[^>]*>(.*?)</div>\s*</div>',
            page,
            re.DOTALL | re.IGNORECASE,
        )

        if not blocks:

            blocks = re.findall(
                r'(<a[^>]+class="result__a".*?</a>)',
                page,
                re.DOTALL | re.IGNORECASE,
            )

        for block in blocks:

            # ------------------------------------------
            # Title
            # ------------------------------------------

            title_match = re.search(
                r'class="result__a"[^>]*>'
                r'(.*?)'
                r'</a>',
                block,
                re.DOTALL | re.IGNORECASE,
            )

            if not title_match:
                continue

            title = self._clean_html(
                title_match.group(1)
            )

            # ------------------------------------------
            # URL
            # ------------------------------------------

            url_match = re.search(
                r'class="result__a"'
                r'[^>]+href="([^"]+)"',
                block,
                re.IGNORECASE,
            )

            if not url_match:
                continue

            raw_url = html.unescape(
                url_match.group(1)
            )

            real_url = self._decode_url(
                raw_url
            )

            # ------------------------------------------
            # Snippet
            # ------------------------------------------

            snippet_match = re.search(
                r'class="result__snippet"'
                r'[^>]*>'
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

                snippet = (
                    "No description available."
                )

            results.append(
                {
                    "title": title,
                    "snippet": snippet,
                    "url": real_url,
                }
            )

        return results

    # ==================================================
    # Decode DuckDuckGo Redirect
    # ==================================================

    @staticmethod
    def _decode_url(
        url,
    ):

        if "uddg=" in url:

            parsed = urllib.parse.urlparse(
                "https:" + url
                if url.startswith("//")
                else url
            )

            query = urllib.parse.parse_qs(
                parsed.query
            )

            if "uddg" in query:

                return query["uddg"][0]

        return url

    # ==================================================
    # Clean HTML
    # ==================================================

    @staticmethod
    def _clean_html(
        text,
    ):

        text = html.unescape(
            text
        )

        text = re.sub(
            r"<[^>]+>",
            "",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()