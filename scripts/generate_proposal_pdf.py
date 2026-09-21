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
        margin: 15mm 15mm 15mm 15mm;
        size: A4;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1f2328;
        background-color: #ffffff;
        line-height: 1.5;
        font-size: 10pt;
    }
    h1 {
        color: #0f172a;
        font-size: 17pt;
        border-bottom: 2px solid #d97706;
        padding-bottom: 4px;
        margin-top: 6px;
        margin-bottom: 8px;
    }
    h2 {
        color: #1e293b;
        font-size: 12.5pt;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 4px;
        margin-top: 14px;
        margin-bottom: 6px;
    }
    h3 {
        color: #334155;
        font-size: 10.5pt;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    p {
        margin-top: 0;
        margin-bottom: 6px;
        font-size: 9.5pt;
    }
    ul, ol {
        margin-top: 2px;
        margin-bottom: 6px;
        padding-left: 20px;
        font-size: 9.5pt;
    }
    li {
        margin-bottom: 3px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 8px 0;
        font-size: 9pt;
    }
    th, td {
        border: 1px solid #cbd5e1;
        padding: 5px 8px;
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
        font-size: 8.5pt;
        background-color: #f1f5f9;
        padding: 2px 4px;
        border-radius: 3px;
    }
    pre {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 6px 10px;
        font-family: Menlo, Monaco, Consolas, monospace;
        font-size: 8pt;
        line-height: 1.35;
    }
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 12px 0;
    }
    strong {
        color: #0f172a;
    }
    .badge {
        display: inline-block;
        background-color: #d97706;
        color: #ffffff;
        font-weight: bold;
        font-size: 8pt;
        padding: 2px 6px;
        border-radius: 3px;
        margin-bottom: 6px;
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
