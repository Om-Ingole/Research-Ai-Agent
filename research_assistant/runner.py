import asyncio
import glob
import os
import uuid
from typing import AsyncGenerator

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

APP_NAME = "multi-agent-research"
USER_ID = "portfolio-user"


def _make_session_and_runner() -> tuple:
    service = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=service)
    return service, runner


async def run_research_streaming(topic: str) -> AsyncGenerator[dict, None]:
    """
    Async generator that yields event dicts as the pipeline runs, then a
    final {"type": "result", "data": {...}} dict.

    Event dict shapes:
      {"type": "agent_start",  "agent": str}
      {"type": "text",         "agent": str, "chunk": str}
      {"type": "tool_call",    "agent": str, "tool": str, "args": dict}
      {"type": "tool_done",    "agent": str, "tool": str}
      {"type": "result",       "data": {"final_report", "raw_research", "analysis"}}
    """
    session_service, runner = _make_session_and_runner()
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=f"Research this topic thoroughly: {topic}")],
    )

    current_author = None

    async for event in runner.run_async(
        user_id=USER_ID, session_id=session_id, new_message=message,
    ):
        author = event.author or ""

        if author and author != current_author:
            current_author = author
            yield {"type": "agent_start", "agent": author}

        if not event.content or not event.content.parts:
            continue

        for part in event.content.parts:
            fc = getattr(part, "function_call", None)
            fr = getattr(part, "function_response", None)
            text = getattr(part, "text", None)

            if fc and getattr(fc, "name", None):
                args = {}
                try:
                    if fc.args:
                        args = dict(fc.args)
                except Exception:
                    pass
                yield {"type": "tool_call", "agent": author, "tool": fc.name, "args": args}

            elif fr and getattr(fr, "name", None):
                yield {"type": "tool_done", "agent": author, "tool": fr.name}

            elif text:
                yield {"type": "text", "agent": author, "chunk": text}

        # Emit token usage whenever the model reports it
        u = event.usage_metadata
        if u and u.total_token_count:
            yield {
                "type": "token_usage",
                "agent": author,
                "prompt_tokens": u.prompt_token_count or 0,
                "output_tokens": u.candidates_token_count or 0,
                "thoughts_tokens": u.thoughts_token_count or 0,
                "cached_tokens": u.cached_content_token_count or 0,
                "total_tokens": u.total_token_count or 0,
            }

    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id,
    )
    state = session.state if session else {}

    # output_key captures the WriterAgent's last text response, which is the
    # short save_report confirmation, not the full report. Read from disk instead.
    final_report = state.get("final_report", "")
    if len(final_report) < 200:
        md_files = glob.glob("outputs/*.md")
        if md_files:
            latest = max(md_files, key=os.path.getmtime)
            try:
                with open(latest, encoding="utf-8") as f:
                    final_report = f.read()
            except Exception:
                pass

    yield {
        "type": "result",
        "data": {
            "final_report": final_report,
            "raw_research": state.get("raw_research", ""),
            "analysis": state.get("analysis", ""),
        },
    }


async def run_research_async(topic: str) -> dict:
    result = {}
    async for ev in run_research_streaming(topic):
        if ev["type"] == "result":
            result = ev["data"]
    return result


def run_research(topic: str) -> dict:
    """Synchronous wrapper for use in CLI."""
    return asyncio.run(run_research_async(topic))
