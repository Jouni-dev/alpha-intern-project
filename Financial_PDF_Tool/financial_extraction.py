"""
Financial PDF Extraction Module

Extracts financial line items from the PDF using regex-based text parsing
instead of pdfplumber's table detection (this PDF has real text but no
ruled table lines, so extract_tables() finds nothing on pages 1-3).

Skips page 4 (revenue/expense chart - no extractable table data).
"""

import re
import pdfplumber
from typing import List, Dict, Any

print("[financial_extraction] Module loaded")

# Money (1,234.56 / -1,234.56), percentages (12.34% / 5,660.00%),
# and short footnote markers like (a), (aa) - not longer words like (current)
TOKEN_PATTERN = r'-?[\d,]+\.\d+%|-?[\d,]+\.\d+|\([a-z]{1,2}\)'

# Lines that mark the end of the data table (recap/footnote prose follows)
STOP_MARKERS = [
    "Mid-Year Financial Statement Recap",
    "Year Over Year Recap",
    "Notes (Variances",
    "Notes:",
]

SKIP_EXACT = [
    "Wikimedia Foundation",
    "Actual vs Plan Comparison",
    "Year-Over-Year Comparison",
    "Balance Sheet",
    "Actual Plan Annual",
]

SECTION_HEADERS = [
    "Ordinary Income/Expense", "Income", "Expense",
    "ASSETS", "Current Assets", "Other Assets",
    "LIABILITIES & EQUITY", "Current Liabilities", "Equity",
]

REPORT_CONFIG = {
    "Actual_vs_Plan": {
        "title": "Actual vs Plan (Jul-Dec 2008)",
        "columns": ["Actual (Jul-Dec 08)", "Plan (Jul-Dec 08)", "$ Change", "% Change", "Annual Plan"]
    },
    "Year_over_Year": {
        "title": "Year-over-Year Comparison (Jul-Dec 2008 vs 2007)",
        "columns": ["Jul-Dec 08", "Jul-Dec 07", "$ Change", "% Change"]
    },
    "Balance_Sheet": {
        "title": "Balance Sheet (as of Dec 31, 2008)",
        "columns": ["Dec 31, 08", "Dec 31, 07", "$ Change", "% Change"]
    }
}


def detect_report_type(text: str) -> str:
    """Detect which financial report a page contains, from its text."""
    if "Actual vs Plan" in text:
        return "Actual_vs_Plan"
    elif "Year-Over-Year" in text:
        return "Year_over_Year"
    elif "Balance Sheet" in text:
        return "Balance_Sheet"
    else:
        return "Unknown"


def is_column_header_row(line: str) -> bool:
    return "$ Change" in line and "% Change" in line


def is_title_line(line: str) -> bool:
    if line in SKIP_EXACT:
        return True
    if re.match(r'^(July \d|As of|Year-to-Date)', line):
        return True
    return False


def parse_page_lines(text: str) -> List[Dict[str, Any]]:
    """Parse a page's extracted text into structured rows."""
    lines = text.split("\n")
    rows = []
    current_section = None
    pending_label = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(line.startswith(marker) for marker in STOP_MARKERS):
            break

        if is_title_line(line) or is_column_header_row(line):
            continue

        if line in SECTION_HEADERS:
            current_section = line
            pending_label = ""
            continue

        tokens = re.findall(TOKEN_PATTERN, line)

        if not tokens:
            # wrapped label continuation - numbers appear on the next line
            pending_label = (pending_label + " " + line).strip()
            continue

        first_token_match = re.search(TOKEN_PATTERN, line)
        label_part = line[:first_token_match.start()].strip()
        full_label = (pending_label + " " + label_part).strip() if pending_label else label_part
        pending_label = ""

        if not re.search(r'[A-Za-z]', full_label):
            continue

        rows.append({
            "section": current_section,
            "label": full_label,
            "tokens": tokens,
        })

    return rows


def build_chunk_text(row: Dict[str, Any], report_type: str) -> str:
    """Format a parsed row into a single embeddable string."""
    cfg = REPORT_CONFIG[report_type]
    notes = [t for t in row["tokens"] if t.startswith("(")]
    values = [t for t in row["tokens"] if not t.startswith("(")]

    parts = [f"Report: {cfg['title']}"]
    if row["section"]:
        parts.append(f"Section: {row['section']}")
    parts.append(f"Account: {row['label']}")

    for col_name, val in zip(cfg["columns"], values):
        parts.append(f"{col_name}: {val}")

    if notes:
        parts.append(f"Notes: {', '.join(notes)}")

    return " | ".join(parts)


def extract_financial_chunks(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract all financial line items from the PDF as embeddable chunks.
    Each chunk: {text, page, report_type, table_index, row_index, section, account_label}
    """
    chunks = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"[financial_extraction] Opened PDF: {len(pdf.pages)} pages")

        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                print(f"[financial_extraction] Page {page_num + 1}: no text, skipping")
                continue

            report_type = detect_report_type(text)
            print(f"[financial_extraction] Page {page_num + 1}: {report_type}")

            if report_type == "Unknown":
                print(f"[financial_extraction] Page {page_num + 1}: skipping (chart/non-tabular page)")
                continue

            rows = parse_page_lines(text)
            print(f"[financial_extraction] Page {page_num + 1}: parsed {len(rows)} rows")

            for row_idx, row in enumerate(rows):
                chunk_text = build_chunk_text(row, report_type)
                chunks.append({
                    "text": chunk_text,
                    "page": page_num + 1,
                    "report_type": report_type,
                    "table_index": 0,
                    "row_index": row_idx,
                    "section": row["section"],
                    "account_label": row["label"],
                })

    print(f"[financial_extraction] Total chunks extracted: {len(chunks)}")
    return chunks


# Alias for compatibility with financial_retrieval.py
def extract_tables_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    return extract_financial_chunks(pdf_path)


if __name__ == "__main__":
    pdf_path = "./mid_Financial.pdf"

    print("[__main__] Starting PDF extraction...\n")
    chunks = extract_financial_chunks(pdf_path)

    print(f"\n[__main__] Extracted {len(chunks)} total chunks")

    if chunks:
        print("\n[__main__] Sample chunks (first 5):")
        for i, chunk in enumerate(chunks[:5]):
            print(f"\nChunk {i+1}:")
            print(f"  Page: {chunk['page']}")
            print(f"  Report: {chunk['report_type']}")
            print(f"  Section: {chunk['section']}")
            print(f"  Text: {chunk['text']}")

        print(f"\n[__main__] Breakdown by report type:")
        by_type = {}
        for c in chunks:
            by_type[c["report_type"]] = by_type.get(c["report_type"], 0) + 1
        for rtype, count in by_type.items():
            print(f"  {rtype}: {count} chunks")