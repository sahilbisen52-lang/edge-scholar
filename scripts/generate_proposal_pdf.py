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
        margin: 12mm 14mm 12mm 14mm;
        size: A4;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1f2328;
        background-color: #ffffff;
        line-height: 1.42;
        font-size: 9.5pt;
    }
    h1 {
        color: #0f172a;
        font-size: 16pt;
        border-bottom: 2px solid #d97706;
        padding-bottom: 3px;
        margin-top: 4px;
        margin-bottom: 6px;
    }
    h2 {
        color: #1e293b;
        font-size: 11.5pt;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 3px;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    h3 {
        color: #334155;
        font-size: 10pt;
        margin-top: 8px;
        margin-bottom: 3px;
    }
    p {
        margin-top: 0;
        margin-bottom: 5px;
        font-size: 9.5pt;
    }
    ul, ol {
        margin-top: 2px;
        margin-bottom: 5px;
        padding-left: 18px;
        font-size: 9.5pt;
    }
    li {
        margin-bottom: 2px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 6px 0;
        font-size: 8.5pt;
    }
    th, td {
        border: 1px solid #cbd5e1;
        padding: 4px 7px;
        text-align: left;
    }
    th {
        background-color: #f1f5f9;
        font-weight: 600;
        color: #0f172a;
    }
    tr:nth-child(even) {
        background-color: #f8fafc;
    }
    code {
        font-family: Menlo, Monaco, Consolas, monospace;
        font-size: 8pt;
        background-color: #f1f5f9;
        padding: 1px 3px;
        border-radius: 3px;
    }
    pre {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 5px 8px;
        margin: 4px 0;
        font-family: Menlo, Monaco, Consolas, monospace;
        font-size: 7.5pt;
        line-height: 1.3;
    }
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 8px 0;
    }
    strong {
        color: #0f172a;
    }
    .badge {
        display: inline-block;
        background-color: #d97706;
        color: #ffffff;
        font-weight: bold;
        font-size: 7.5pt;
        padding: 2px 6px;
        border-radius: 3px;
        margin-bottom: 4px;
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
    <div class="badge">Qualcomm Snapdragon AI Lab Challenge 2026</div>
    {rendered_body}
</body>
</html>"""

    # Save HTML
    html_out_path.write_text(full_html, encoding="utf-8")
    print(f"✅ Generated HTML: {html_out_path}")

    # Generate PDF via Qt6 with ScreenResolution
    app = QGuiApplication.instance() or QGuiApplication([])
    doc = QTextDocument()
    doc.setHtml(full_html)

    printer = QPrinter(QPrinter.ScreenResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(str(pdf_out_path))

    doc.print_(printer)
    print(f"✅ Generated PDF:  {pdf_out_path} ({pdf_out_path.stat().st_size // 1024} KB)")

    return pdf_out_path, html_out_path


if __name__ == "__main__":
    generate_proposal_documents()
