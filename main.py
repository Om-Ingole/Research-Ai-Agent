#!/usr/bin/env python3
"""
CLI entry point for testing the research pipeline.
Usage: python main.py "your research topic"
       python main.py "Impact of AI agents on data science jobs"
"""

import sys
import time

from dotenv import load_dotenv

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py \"your research topic here\"")
        print('Example: python main.py "Google ADK multi-agent systems"')
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    print(f"\nStarting 3-agent research pipeline")
    print(f"Topic: {topic}")
    print("=" * 60)
    print("Agent 1: ResearcherAgent (searching + scraping web)...")

    from research_assistant.runner import run_research

    start = time.time()
    result = run_research(topic)
    elapsed = round(time.time() - start, 1)

    print("\n" + "=" * 60)
    print(f"Pipeline complete in {elapsed}s")
    print("=" * 60)
    print("\nFINAL REPORT:")
    print(result["final_report"])
    print("\n[Raw research and analysis saved in session state]")


if __name__ == "__main__":
    main()
