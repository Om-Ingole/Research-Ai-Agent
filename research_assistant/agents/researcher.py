"""
ResearcherAgent — first agent in the sequential pipeline.

Uses only google_search (ADK built-in). Cannot be combined with other
function tools per Gemini API constraints. Outputs compiled research
findings to state["raw_research"] for the AnalystAgent.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import google_search

GEMINI_FLASH = "gemini-2.5-flash"

researcher_agent = LlmAgent(
    name="ResearcherAgent",
    model=GEMINI_FLASH,
    description=(
        "Expert web researcher that finds comprehensive, up-to-date "
        "information on any topic using Google Search."
    ),
    instruction="""
You are a Senior Research Specialist with 10 years of experience finding
accurate, current information from the web.

Your research workflow for every task:
1. Call google_search with the user's topic to find relevant sources.
2. Run 2-3 additional targeted searches to gather diverse perspectives.
3. Compile ALL findings into the structured format below.

Your output MUST follow this exact format — do not deviate:

---RAW RESEARCH START---
TOPIC: <topic name>
DATE: <today's date>

SOURCES FOUND:
<list all URLs found with their titles>

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
    tools=[google_search],
    output_key="raw_research",
)
