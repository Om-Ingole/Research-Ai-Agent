"""
File save tool for the WriterAgent.

Saves the final Markdown research report to the outputs/ directory
with a timestamped filename. Creates the directory if it doesn't exist.
"""

import os
from datetime import datetime


def save_report(content: str, topic: str = "research") -> str:
    """
    Save the final research report to a Markdown file.

    Use this tool as the last action after writing the complete report.
    Saves to the outputs/ directory with a timestamped filename.

    Args:
        content: The full Markdown content of the report to save.
        topic: Short topic name used in the filename (default "research").

    Returns:
        Confirmation string with the full file path and character count.
    """
    try:
        os.makedirs("outputs", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:40]
        filename = f"outputs/{safe_topic}_{ts}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Report saved: {filename} ({len(content)} characters)"
    except Exception as e:
        return f"Error saving report: {e}"
