"""
Script to generate a professional PDF and standalone HTML document of the
EdgeScholar Official Proposal Submission.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from markdown_it import MarkdownIt
from PySide6.QtGui import QGuiApplication, QTextDocument
from PySide6.QtPrintSupport import QPrinter

CSS_STYLES = """
<style>
    @page {
        margin: 20mm 15mm 20mm 15mm;
        size: A4;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #222222;
        background-color: #ffffff;
        line-height: 1.55;
        font-size: 13px;
        margin: 20px 30px;
    }
    h1 {
        color: #111111;
        font-size: 24px;
        border-bottom: 2px solid #c47d2b;
        padding-bottom: 8px;
        margin-top: 20px;
        margin-bottom: 12px;
    }
    h2 {
        color: #1c1c1e;
        font-size: 18px;
        border-bottom: 1px solid #e5e5ea;
        padding-bottom: 6px;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    h3 {
        color: #2c2c2e;
        font-size: 15px;
        margin-top: 14px;
        margin-bottom: 6px;
    }
    p {
        margin-top: 0;
        margin-bottom: 10px;
    }
    ul, ol {
        margin-top: 4px;
        margin-bottom: 10px;
        padding-left: 24px;
    }
    li {
        margin-bottom: 4px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 14px 0;
        font-size: 12px;
    }
    th, td {
        border: 1px solid #d1d1d6;
        padding: 8px 12px;
        text-align: left;
    }
    th {
        background-color: #f2f2f7;
        font-weight: 600;
        color: #1c1c1e;
    }
    tr:nth-child(even) {
        background-color: #fafafa;
    }
    code {
        font-family: "SF Mono", Menlo, Consolas, Monaco, monospace;
        font-size: 11.5px;
        background-color: #f2f2f7;
        padding: 2px 5px;
        border-radius: 4px;
    }
    pre {
        background-color: #f7f7f8;
        border: 1px solid #e5e5ea;
        border-radius: 6px;
        padding: 12px;
        overflow-x: auto;
        font-family: "SF Mono", Menlo, Consolas, Monaco, monospace;
        font-size: 11px;
        line-height: 1.45;
    }
    hr {
        border: none;
        border-top: 1px solid #e5e5ea;
        margin: 20px 0;
    }
    strong {
        color: #111111;
    }
    .header-badge {
        display: inline-block;
        background-color: #c47d2b;
        color: #ffffff;
        font-weight: bold;
        font-size: 11px;
        padding: 3px 8px;
        border-radius: 4px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
"""


def generate_proposal_documents() -> tuple[Path, Path]:
    proposal_md_path = PROJECT_ROOT / "docs" / "PROPOSAL_SUBMISSION.md"
    pdf_out_path = PROJECT_ROOT / "docs" / "EdgeScholar_Proposal.pdf"
    html_out_path = PROJECT_ROOT / "docs" / "EdgeScholar_Proposal.html"

    if not proposal_md_path.exists():
        raise FileNotFoundError(f"Missing {proposal_md_path}")

    md_text = proposal_md_path.read_text(encoding="utf-8")
    md = MarkdownIt("commonmark", {"breaks": False, "html": True})
    rendered_body = md.render(md_text)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>EdgeScholar — Proposal Submission</title>
    {CSS_STYLES}
</head>
<body>
    <div class="header-badge">Qualcomm Snapdragon AI Lab Challenge 2026</div>
    {rendered_body}
</body>
</html>"""

    # Save HTML
    html_out_path.write_text(full_html, encoding="utf-8")
    print(f"✅ Generated HTML: {html_out_path}")

    # Generate PDF via Qt6 offscreen
    app = QGuiApplication.instance() or QGuiApplication([])
    doc = QTextDocument()
    doc.setHtml(full_html)

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(str(pdf_out_path))

    doc.print_(printer)
    print(f"✅ Generated PDF:  {pdf_out_path} ({pdf_out_path.stat().st_size // 1024} KB)")

    return pdf_out_path, html_out_path


if __name__ == "__main__":
    generate_proposal_documents()
