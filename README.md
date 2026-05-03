# Multi-Agent AI Research Assistant (Google ADK)

![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue)
![Google ADK](https://img.shields.io/badge/Google%20ADK-latest-green)
![Gemini 2.5](https://img.shields.io/badge/Gemini-2.5-orange)
![SequentialAgent](https://img.shields.io/badge/Agent-SequentialAgent-purple)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![License](https://img.shields.io/badge/License-Apache%202.0-lightgrey)

A production-ready multi-agent AI system that researches any topic by orchestrating three specialized Gemini-powered agents via Google ADK's `SequentialAgent`. Given a topic, it searches the web via Google Search grounding, extracts insights, and produces a polished Markdown report — fully autonomously, with a real-time streaming UI and per-agent token usage tracking.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Getting a Google API Key](#getting-a-google-api-key)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the App](#running-the-app)
6. [How It Works](#how-it-works)
7. [Architecture](#architecture)
8. [Agents & Tools](#agents--tools)
9. [Streamlit UI Features](#streamlit-ui-features)
10. [Project Structure](#project-structure)
11. [Troubleshooting](#troubleshooting)
12. [What This Demonstrates](#what-this-demonstrates)

---

## Prerequisites

Before you start, make sure you have the following installed:

### 1. Python 3.11 or higher

Check your version:
```bash
python --version
```

If you don't have Python 3.11+, download it from [python.org](https://www.python.org/downloads/).

### 2. uv (Python package manager)

This project uses `uv` for dependency management. Install it with:

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify the install:
```bash
uv --version
```

### 3. Git

Download from [git-scm.com](https://git-scm.com/downloads) if not already installed.

---

## Getting a Google API Key

This project uses **Gemini 2.5** models via the Google AI Studio API. The same key enables the native Google Search grounding tool — no separate Search API needed.

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **"Get API key"** → **"Create API key"**
4. Copy the key — you'll add it to `.env` in the next step

> The free tier includes generous limits suitable for development and testing.

---

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd Research-Ai-Agent
```

### 2. Install all dependencies

`uv` creates an isolated virtual environment (`.venv/`) automatically:

```bash
uv sync
```

This installs everything listed in `pyproject.toml`, including:
- `google-adk` — the Google Agent Development Kit
- `streamlit` — the web UI
- `python-dotenv` — environment variable loading
- `playwright`, `beautifulsoup4`, `requests` — web tooling (used by optional scraper tool)

---

## Configuration

### 1. Create your `.env` file

```bash
cp .env.example .env
```

### 2. Add your API key

Open `.env` and set your key:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

> **`GOOGLE_GENAI_USE_VERTEXAI=FALSE`** tells the SDK to use AI Studio (not Google Cloud Vertex AI). Keep this as-is unless you have a Vertex AI setup.

The `.env` file is gitignored — your key will never be committed.

---

## Running the App

### Option A — Streamlit UI (recommended)

The full experience: real-time event streaming, token usage cards, downloadable reports.

```bash
uv run streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Option B — ADK built-in web UI

Useful for debugging individual agents and inspecting session state.

```bash
uv run adk web
```

Open [http://localhost:8000](http://localhost:8000), select **"ResearchPipeline"**, and send a message.

### Option C — Command line

```bash
uv run python main.py "Impact of AI agents on data science jobs 2026"
```

The report is printed to stdout and saved to `outputs/`.

---

## How It Works

Enter any research topic and click **Run Research Pipeline**. Three Gemini agents then work in sequence, each handing its output to the next via ADK session state:

```
You type: "Best practices for RAG systems in production"
         ↓
🔬 ResearcherAgent   — searches Google, compiles raw findings
         ↓  state["raw_research"]
📊 AnalystAgent      — reads findings, extracts 5 key insights
         ↓  state["analysis"]
✍️ WriterAgent        — reads both, writes a full Markdown report
         ↓
📄 Report displayed in browser + saved to outputs/
```

The Streamlit UI streams each ADK event in real time — you see each agent activate, its current output line scroll by, and tool calls fire (e.g. `💾 Saving report…`) as they happen.

---

## Architecture

```
User query
    ↓
SequentialAgent ("ResearchPipeline")
    ↓
ResearcherAgent          ← google_search (ADK built-in grounding tool)
    ↓ output_key="raw_research" → session.state
AnalystAgent             ← reads {raw_research} via template injection
    ↓ output_key="analysis" → session.state
WriterAgent              ← reads {raw_research} + {analysis}, calls save_report
    ↓ saves to outputs/*.md
Markdown Report (rendered in Streamlit + downloaded as .md)
```

**State passing pattern:** Each agent writes its output to session state via `output_key`. Downstream agents read it through `{variable_name}` template injection in their instruction strings — the canonical ADK approach.

**No LLM routing:** `SequentialAgent` executes sub-agents in a fixed order. There is no LLM deciding what runs next — execution is deterministic.

---

## Agents & Tools

### Agents

| Agent | Model | Role | Tools |
|-------|-------|------|-------|
| ResearcherAgent | `gemini-2.5-flash` | Web research via Google Search grounding | `google_search` (ADK built-in) |
| AnalystAgent | `gemini-2.5-flash` | Insight extraction & synthesis | none (text-only) |
| WriterAgent | `gemini-2.5-pro` | Report generation + file save | `save_report` |

### Tools

| Tool | Location | Description |
|------|----------|-------------|
| `google_search` | ADK built-in | Gemini 2 native Google Search grounding — no separate API key required |
| `save_report` | `tools/file_tool.py` | Saves the Markdown report to `outputs/` with a timestamped filename |

### Important: `google_search` constraint

The ADK/Gemini built-in `google_search` tool **cannot be combined with other function-calling tools** in the same agent. This is a Gemini API constraint — built-in grounding tools and custom function tools cannot share a single agent. The search happens entirely within the Gemini model; no local code executes for the search step.

---

## Streamlit UI Features

| Feature | Description |
|---------|-------------|
| **Real-time streaming** | Each ADK event (agent start, tool call, text chunk) updates the UI live — no waiting for pipeline completion |
| **Live text preview** | The last line of the active agent's output scrolls in place as tokens stream in |
| **Tool call display** | `💾 Saving report…` and `✅ save_report complete` appear as they fire |
| **Token usage cards** | Color-coded per-agent breakdown: input, output, thinking, cached, and total tokens |
| **Total token metric** | Grand total displayed in the right panel alongside research time |
| **Download report** | Exports the full Markdown report as a `.md` file |
| **Expandable raw outputs** | View Agent 1's raw research and Agent 2's analysis with full Markdown rendering |
| **Session history** | Tracks the last 5 research topics in the current session |
| **Example topics** | One-click buttons to pre-fill common research topics |

---

## Project Structure

```
Research-Ai-Agent/
├── research_assistant/          ← Python package (importable by adk web)
│   ├── __init__.py              ← Exports root_agent
│   ├── agent.py                 ← Defines root_agent (SequentialAgent, 3 agents)
│   ├── runner.py                ← Async streaming generator + sync CLI wrapper
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── researcher.py        ← ResearcherAgent (google_search built-in)
│   │   ├── analyst.py           ← AnalystAgent (insight extraction, no tools)
│   │   └── writer.py            ← WriterAgent (report generation, save_report)
│   └── tools/
│       ├── __init__.py
│       └── file_tool.py         ← save_report() — writes timestamped .md to outputs/
├── app.py                       ← Streamlit UI with real-time streaming + token cards
├── main.py                      ← CLI entry point
├── outputs/                     ← Generated .md reports (gitignored)
├── .env                         ← Your API keys (gitignored — never committed)
├── .env.example                 ← Template — copy this to .env
├── .gitignore
├── pyproject.toml               ← uv-managed dependencies
├── uv.lock                      ← Locked dependency versions
└── README.md
```

---

## Troubleshooting

### `GOOGLE_API_KEY` not found / authentication error

- Make sure `.env` exists and contains `GOOGLE_API_KEY=your_key_here`
- Confirm the key is valid at [aistudio.google.com](https://aistudio.google.com)
- The `.env` file must be in the project root (same folder as `app.py`)

### `Pipeline error: 400 INVALID_ARGUMENT` — built-in tools and function calling

This happens if a custom function tool is added to `ResearcherAgent` alongside `google_search`. The Gemini API does not allow combining grounding tools with function-calling tools. Keep `ResearcherAgent` with `google_search` as its only tool.

### `Context variable not found: <name>`

An agent instruction contains `{variable_name}` but that variable isn't in session state. Common cause: a previous agent failed to write its `output_key`. Check that each agent's instruction only uses `{raw_research}` and `{analysis}` as template variables, and that all other `{...}` placeholders use angle brackets (`<placeholder>`) instead.

### Report file is empty after download

The `outputs/` directory must be writable. If `save_report` fails, check the error in the Streamlit status panel. The runner automatically falls back to reading the most recently saved `.md` file from `outputs/`.

### `uv sync` fails

- Make sure you have Python 3.11+ on your system path
- Try `uv python install 3.12` then `uv sync` again

### Streamlit widget key warning

If you see a warning about a widget with a default value and a session state key, ensure `st.text_input` does not set both `value=` and `key=` to the same session state entry simultaneously.

---

## What This Demonstrates

| Concept | Implementation |
|---------|---------------|
| Google ADK `SequentialAgent` | Deterministic 3-agent pipeline with no LLM routing |
| State passing between agents | `output_key` writes → `{template_injection}` reads in instruction strings |
| ADK built-in tools | `google_search` grounding — why it can't combine with function tools |
| Custom function tools | `save_report` — plain Python function auto-wrapped by ADK via type hints + docstring |
| Real-time event streaming | Async generator over ADK events, bridged to Streamlit via `threading.Thread` + `queue.Queue` |
| Async/sync boundary | `asyncio.run()` in a background thread; Streamlit's main thread consumes the queue |
| Token usage tracking | `event.usage_metadata` parsed per agent; displayed as styled HTML cards |
| Multi-agent context chaining | Each agent reads and builds on previous agent's session state |
| Report recovery from disk | `output_key` captures only the last response; full report read from saved `.md` file |

---

## License

Apache 2.0
