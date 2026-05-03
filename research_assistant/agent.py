from google.adk.agents import SequentialAgent

from .agents.analyst import analyst_agent
from .agents.researcher import researcher_agent
from .agents.writer import writer_agent

# Pipeline: ResearcherAgent → AnalystAgent → WriterAgent
# google_search cannot share an agent with other function tools (Gemini API
# constraint), so scraping is handled by the LLM via grounding instead.
root_agent = SequentialAgent(
    name="ResearchPipeline",
    description=(
        "A 3-agent research pipeline. Given a topic, it searches the web, "
        "analyses findings, and writes a polished Markdown report."
    ),
    sub_agents=[
        researcher_agent,  # google_search → state["raw_research"]
        analyst_agent,     # reads state["raw_research"] → state["analysis"]
        writer_agent,      # reads both → state["final_report"]
    ],
)
