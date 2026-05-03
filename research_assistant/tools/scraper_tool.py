"""
Web scraper tool for the ResearcherAgent.

Uses Playwright (async, headless Chromium) to render and extract full
page text content, including JavaScript-rendered pages. The async
implementation is wrapped in asyncio.run() for synchronous ADK usage.
"""

import asyncio
from playwright.async_api import async_playwright


async def _scrape(url: str, max_chars: int) -> str:
    """Internal async scraping implementation."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            text = await page.inner_text("body")
            text = "\n".join(
                line.strip() for line in text.splitlines() if line.strip()
            )
            if len(text) > max_chars:
                text = text[:max_chars] + "\n... [content truncated]"
            return text
        except Exception as e:
            return f"Error scraping {url}: {e}"
        finally:
            await browser.close()


def scrape_webpage(url: str, max_chars: int = 3000) -> str:
    """
    Scrape and return the main text content from a webpage URL.

    Use this tool to get the full content of a specific webpage after
    finding its URL via web_search. Handles JavaScript-rendered pages.

    Args:
        url: The full URL of the webpage to scrape (must start with
             http:// or https://).
        max_chars: Maximum characters to return (default 3000).

    Returns:
        Cleaned text content of the page, or an error message string
        if the page cannot be loaded.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already inside an async context (e.g., ADK runner) —
        # run in a separate thread to avoid "event loop already running"
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _scrape(url, max_chars))
            return future.result(timeout=30)
    else:
        return asyncio.run(_scrape(url, max_chars))
