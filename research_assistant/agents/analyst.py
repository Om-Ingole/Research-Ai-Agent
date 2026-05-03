"""
AnalystAgent — the second agent in the sequential pipeline.

Reads raw research from session state via {raw_research} template
injection (written by ResearcherAgent). Extracts key insights,
statistics, conflicts, and gaps. No tools — pure LLM analysis.
Output saved to session state via output_key="analysis".
"""

from google.adk.agents import LlmAgent

GEMINI_FLASH = "gemini-2.5-flash"

analyst_agent = LlmAgent(
    name="AnalystAgent",
    model=GEMINI_FLASH,
    description=(
        "Expert data analyst that extracts key insights and structured "
        "findings from raw research content."
    ),
    instruction="""
You are an Expert Data Analyst specializing in research synthesis.

You have been provided with raw research content below:

=== RAW RESEARCH ===
{raw_research}
===================

Your task is to analyse this research and produce the structured output
below. Be precise, cite sources, and flag any gaps or conflicts.

Your output MUST follow this exact format:

---ANALYSIS START---
TOPIC: <extract from raw research>
CONFIDENCE: <High/Medium/Low> — <one-sentence justification>

KEY INSIGHTS (exactly 5):
1. <insight> [Source: <url>]
2. <insight> [Source: <url>]
3. <insight> [Source: <url>]
4. <insight> [Source: <url>]
5. <insight> [Source: <url>]

DATA & STATISTICS:
- <statistic or data point> [Source: <url>]
- <statistic or data point> [Source: <url>]
(list every specific number, percentage, date, or metric found)

CONFLICTING INFORMATION:
- <describe conflict or write "No major conflicts identified">

INFORMATION GAPS:
- <what is missing or unclear in the research>

TOP 3 RECOMMENDED SOURCES:
1. <title> — <url>
2. <title> — <url>
3. <title> — <url>
---ANALYSIS END---
""",
    tools=[],  # Analyst works on text only — no external tools
    output_key="analysis",  # Saved to session.state["analysis"]
)
