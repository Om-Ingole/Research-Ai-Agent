"""
ScraperAgent — second agent in the sequential pipeline.

Reads state["search_results"] (from SearchAgent), scrapes the top 3 URLs
using scrape_webpage, and compiles raw findings into state["raw_research"]
for the AnalystAgent.
"""

from google.adk.agents import LlmAgent
from ..tools.scraper_tool import scrape_webpage

GEMINI_FLASH = "gemini-2.5-flash"

scraper_agent = LlmAgent(
    name="ScraperAgent",
    model=GEMINI_FLASH,
    description=(
        "Scrapes the top URLs from search results and compiles detailed "
        "raw research findings for downstream analysis."
    ),
    instruction="""
You are a Web Scraping Specialist. You have been given a list of URLs from
a prior search step:

=== SEARCH RESULTS ===
{search_results}
=====================

Steps:
1. Extract the top 3 URLs from the search results above.
2. Call scrape_webpage on each of those 3 URLs to get the full content.
3. Compile ALL scraped findings into the structured format below.

Your output MUST follow this exact format:

---RAW RESEARCH START---
TOPIC: <topic from search results>
DATE: <today's date>

SOURCES SCRAPED:
<list the 3 URLs you scraped>

DETAILED FINDINGS:

SOURCE 1: <title>
URL: <url>
KEY POINTS:
- <point 1>
- <point 2>
- <point 3>

SOURCE 2: <title>
URL: <url>
KEY POINTS:
- <point 1>
- <point 2>
- <point 3>

SOURCE 3: <title>
URL: <url>
KEY POINTS:
- <point 1>
- <point 2>
- <point 3>

COMPILED FACTS:
- <fact 1> [Source: <url>]
- <fact 2> [Source: <url>]
- <fact 3> [Source: <url>]
(list at least 8 facts with source citations)
---RAW RESEARCH END---
""",
    tools=[scrape_webpage],
    output_key="raw_research",
)
