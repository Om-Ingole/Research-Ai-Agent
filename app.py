import asyncio
import queue
import threading
import time

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Multi-Agent AI Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Agent / tool display metadata ────────────────────────────────────────────

AGENT_META = {
    "ResearcherAgent": ("🔬", "Research Specialist", "Searching Google & synthesizing findings…", "#4A90E2"),
    "AnalystAgent":    ("📊", "Data Analyst",        "Extracting key insights & statistics…",     "#7B68EE"),
    "WriterAgent":     ("✍️", "Technical Writer",    "Writing the Markdown report…",              "#2ECC71"),
}

TOOL_MSGS = {
    "save_report":    lambda a: "💾 Saving report to `outputs/`…",
    "scrape_webpage": lambda a: f"🌐 Scraping `{a.get('url', '')[:60]}`…",
}


# ── Background thread: runs async pipeline, pushes events to a queue ─────────

def _pipeline_thread(topic: str, q: queue.Queue) -> None:
    async def _run():
        from research_assistant.runner import run_research_streaming
        async for ev in run_research_streaming(topic):
            q.put(ev)

    try:
        asyncio.run(_run())
    except Exception as e:
        q.put({"type": "error", "message": str(e)})
    finally:
        q.put({"type": "done"})


# ── Token usage display ───────────────────────────────────────────────────────

def _render_token_usage(token_data: dict) -> None:
    """Render a beautiful per-agent token usage breakdown."""
    if not token_data:
        return

    st.divider()
    st.subheader("📊 Token Usage")

    # Per-agent cards
    agents = list(token_data.keys())
    cols = st.columns(len(agents))

    grand_prompt = grand_output = grand_thoughts = grand_cached = grand_total = 0

    for col, agent in zip(cols, agents):
        d = token_data[agent]
        icon, _, _, color = AGENT_META.get(agent, ("🤖", "", "", "#888"))
        prompt   = d.get("prompt_tokens", 0)
        output   = d.get("output_tokens", 0)
        thoughts = d.get("thoughts_tokens", 0)
        cached   = d.get("cached_tokens", 0)
        total    = d.get("total_tokens", 0)

        grand_prompt   += prompt
        grand_output   += output
        grand_thoughts += thoughts
        grand_cached   += cached
        grand_total    += total

        thoughts_row = (
            f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
            f"border-top:1px solid {color}30'>"
            f"<span style='opacity:.65;font-size:.8em'>💭 Thoughts</span>"
            f"<span style='font-weight:600'>{thoughts:,}</span></div>"
        ) if thoughts else ""

        cached_row = (
            f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
            f"border-top:1px solid {color}30'>"
            f"<span style='opacity:.65;font-size:.8em'>⚡ Cached</span>"
            f"<span style='font-weight:600;color:#F0A500'>{cached:,}</span></div>"
        ) if cached else ""

        col.markdown(f"""
<div style="background:linear-gradient(135deg,{color}18,{color}08);
            border-left:4px solid {color};border-radius:10px;
            padding:16px 18px;height:100%;">
  <div style="font-size:1em;font-weight:700;margin-bottom:12px">{icon} {agent}</div>
  <div style="display:flex;justify-content:space-between;padding:4px 0">
    <span style="opacity:.65;font-size:.8em">📥 Input</span>
    <span style="font-weight:600">{prompt:,}</span>
  </div>
  <div style="display:flex;justify-content:space-between;padding:4px 0;
              border-top:1px solid {color}30">
    <span style="opacity:.65;font-size:.8em">📤 Output</span>
    <span style="font-weight:600">{output:,}</span>
  </div>
  {thoughts_row}
  {cached_row}
  <div style="display:flex;justify-content:space-between;padding:8px 0 2px;
              border-top:2px solid {color}60;margin-top:4px">
    <span style="font-size:.85em;font-weight:700;opacity:.85">Total</span>
    <span style="font-size:1.2em;font-weight:800;color:{color}">{total:,}</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # Grand total summary row
    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
    n = 4 if grand_thoughts else 3
    summary_cols = st.columns(n)
    summary_cols[0].metric("Total Input Tokens",  f"{grand_prompt:,}")
    summary_cols[1].metric("Total Output Tokens", f"{grand_output:,}")
    if grand_thoughts:
        summary_cols[2].metric("Thinking Tokens", f"{grand_thoughts:,}")
    summary_cols[-1].metric("Grand Total", f"{grand_total:,}")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Research Assistant")
    st.caption("Powered by Google ADK + Gemini")
    st.divider()
    st.subheader("How it works")
    st.markdown("""
    **3 agents run in sequence:**

    🔬 **ResearcherAgent**
    - Native Google Search grounding
    - Compiles findings with citations
    - Model: `gemini-2.5-flash`

    📊 **AnalystAgent**
    - Reads raw research from state
    - Extracts 5 key insights
    - Flags data gaps & conflicts
    - Model: `gemini-2.5-flash`

    ✍️ **WriterAgent**
    - Reads research + analysis
    - Writes structured Markdown report
    - Saves to `outputs/`
    - Model: `gemini-2.5-pro`

    **Orchestrator:** `SequentialAgent`
    **Data flow:** `output_key` → `{template}`
    **UI:** Real-time event streaming
    """)
    st.divider()
    st.caption("Stack: Google ADK · Gemini 2.5 · Streamlit")

# ── Main ──────────────────────────────────────────────────────────────────────

st.title("Multi-Agent AI Research Assistant")
st.caption("3 Gemini-powered agents collaborate to research any topic")

st.subheader("Try an example")
examples = [
    "Impact of AI agents on freelance job market 2026",
    "Best practices for RAG systems in production",
    "Multi-agent AI architectures compared",
    "Python vs JavaScript for AI applications",
]
cols = st.columns(len(examples))
for col, example in zip(cols, examples):
    if col.button(example, use_container_width=True):
        st.session_state["topic_input"] = example

topic = st.text_input(
    "Research topic",
    placeholder="Enter any topic to research…",
    key="topic_input",
)

if st.button("Run Research Pipeline", type="primary", use_container_width=True):
    if not topic.strip():
        st.warning("Please enter a research topic.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            with st.status("Pipeline running…", expanded=True) as status:
                q: queue.Queue = queue.Queue()
                t = threading.Thread(target=_pipeline_thread, args=(topic, q), daemon=True)
                start = time.time()
                t.start()

                result = None
                error = None
                token_data: dict = {}

                current_agent = None
                text_accum = ""
                preview_ph = None

                while True:
                    try:
                        ev = q.get(timeout=300)
                    except queue.Empty:
                        error = "Timeout: pipeline exceeded 5 minutes."
                        break

                    etype = ev.get("type")

                    if etype == "done":
                        break

                    elif etype == "error":
                        error = ev.get("message", "Unknown error")
                        break

                    elif etype == "result":
                        result = ev["data"]

                    elif etype == "token_usage":
                        agent = ev["agent"]
                        # Keep the highest total seen (events arrive per streaming chunk)
                        prev = token_data.get(agent, {})
                        if ev.get("total_tokens", 0) >= prev.get("total_tokens", 0):
                            token_data[agent] = ev

                    elif etype == "agent_start":
                        agent = ev["agent"]
                        if preview_ph and text_accum.strip():
                            last_line = next(
                                (l.strip() for l in reversed(text_accum.splitlines()) if l.strip()),
                                "",
                            )
                            preview_ph.caption(f"_{last_line[:120]}_")

                        icon, role, action, _ = AGENT_META.get(agent, ("🤖", agent, "Working…", "#888"))
                        st.markdown(f"**{icon} {agent}** — {role}")
                        st.caption(action)
                        preview_ph = st.empty()
                        text_accum = ""
                        current_agent = agent

                    elif etype == "text":
                        chunk = ev.get("chunk", "")
                        text_accum += chunk
                        lines = [l.strip() for l in text_accum.splitlines() if l.strip()]
                        if lines and preview_ph:
                            preview_ph.markdown(
                                f"<span style='color:grey;font-size:0.85em'>{lines[-1][:160]}</span>",
                                unsafe_allow_html=True,
                            )

                    elif etype == "tool_call":
                        tool = ev.get("tool", "")
                        args = ev.get("args", {})
                        formatter = TOOL_MSGS.get(tool)
                        st.write(formatter(args) if formatter else f"🔧 Calling `{tool}`…")

                    elif etype == "tool_done":
                        st.write(f"✅ `{ev.get('tool', '')}` complete")

                # Freeze last preview
                if preview_ph and text_accum.strip():
                    last_line = next(
                        (l.strip() for l in reversed(text_accum.splitlines()) if l.strip()),
                        "",
                    )
                    preview_ph.caption(f"_{last_line[:120]}_")

                t.join(timeout=5)
                elapsed = round(time.time() - start, 1)

                if error:
                    status.update(label="Pipeline error", state="error", expanded=True)
                    st.error(f"Pipeline error: {error}")
                    st.info("Check your GOOGLE_API_KEY in `.env` and try again.")
                elif result:
                    status.update(
                        label=f"✅ Research complete in {elapsed}s",
                        state="complete",
                        expanded=False,
                    )
                    st.session_state["last_result"] = result
                    st.session_state["last_topic"] = topic
                    st.session_state["last_elapsed"] = elapsed
                    st.session_state["last_tokens"] = token_data
                    if "history" not in st.session_state:
                        st.session_state["history"] = []
                    st.session_state["history"].append(topic)

        with col2:
            elapsed_val = st.session_state.get("last_elapsed", 0)
            tokens = st.session_state.get("last_tokens", {})
            grand_total = sum(d.get("total_tokens", 0) for d in tokens.values())

            st.metric("Research time", f"{elapsed_val}s")
            st.metric("Agents used", "3")
            if grand_total:
                st.metric("Total tokens", f"{grand_total:,}")

# ── Results ───────────────────────────────────────────────────────────────────

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    topic_shown = st.session_state.get("last_topic", "")

    st.divider()
    st.subheader(f"Research Report: {topic_shown}")
    st.markdown(result["final_report"])

    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            label="Download report (.md)",
            data=result["final_report"],
            file_name=f"research_{topic_shown[:30].replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_b:
        if st.button("Clear results", use_container_width=True):
            for key in ("last_result", "last_tokens", "last_elapsed", "last_topic"):
                st.session_state.pop(key, None)
            st.rerun()

    with st.expander("Raw research (Agent 1 output)"):
        st.markdown(result["raw_research"])

    with st.expander("Analysis (Agent 2 output)"):
        st.markdown(result["analysis"])

    # Token usage breakdown
    if st.session_state.get("last_tokens"):
        _render_token_usage(st.session_state["last_tokens"])

# ── History ───────────────────────────────────────────────────────────────────

if st.session_state.get("history"):
    st.divider()
    st.subheader("Previous searches this session")
    for past_topic in reversed(st.session_state["history"][-5:]):
        st.caption(f"— {past_topic}")
