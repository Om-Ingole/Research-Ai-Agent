"""
Web search tool for the ResearcherAgent.

Uses DuckDuckGo (via duckduckgo-search) to find URLs plus titles and snippets.
No API key required. No decorator needed — ADK auto-converts plain Python
functions into FunctionTool using type hints + docstrings.
"""

import warnings

import requests
from bs4 import BeautifulSoup

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from duckduckgo_search import DDGS

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}


def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web for the given query and return structured results.

    Use this tool to find recent information, articles, and sources on
    any topic. Returns a numbered list with title, URL, and snippet for
    each result.

    Args:
        query: The search query string.
        num_results: Number of results to return (default 5, max 10).

    Returns:
        Formatted string with numbered results, each containing title,
        URL, and a short content snippet. Returns an error string if
        the search fails.
    """
    try:
        ddgs_results = DDGS().text(query, max_results=num_results)
    except Exception as e:
        return f"Search failed for '{query}': {e}"

    if not ddgs_results:
        return f"No results found for '{query}'."

    results = [f"Search results for: {query}\nFound {len(ddgs_results)} sources\n"]

    for i, item in enumerate(ddgs_results, 1):
        url = item.get("href", "")
        title = item.get("title", "No title")
        snippet = item.get("body", "")[:300]

        # Try to enrich snippet from the live page if DDG snippet is short
        if len(snippet) < 100 and url:
            try:
                resp = requests.get(url, headers=HEADERS, timeout=5)
                soup = BeautifulSoup(resp.text, "html.parser")
                if soup.title and not title:
                    title = soup.title.string.strip()
                paras = soup.find_all("p")
                live_snippet = " ".join(p.get_text()[:100] for p in paras[:3]).strip()
                if live_snippet:
                    snippet = live_snippet[:300]
            except Exception:
                pass

        snippet = snippet + "..." if len(snippet) >= 300 else snippet
        results.append(
            f"{i}. {title}\n"
            f"   URL: {url}\n"
            f"   Snippet: {snippet}\n"
        )

    return "\n".join(results)
