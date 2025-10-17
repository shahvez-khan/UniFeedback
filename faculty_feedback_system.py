#!/usr/bin/env python3
"""
Faculty Feedback System (Console) - Python

Features:
- Collect ratings from multiple students for a given faculty across categories (1–5 scale)
- Compute per-category averages and overall average
- Print star rating (★/☆) in console
- Generate a nicely formatted PDF report with category-wise averages, overall rating, and stars

Dependencies:
    pip install reportlab

Usage:
    python faculty_feedback_system.py

    The program will prompt you for:
      - Faculty name
      - Number of students providing feedback
      - Each student's ratings for each category (1-5)

PDF Output:
    A PDF named like: feedback_<faculty_name>_<YYYYMMDD_HHMMSS>.pdf

Author: ChatGPT
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from statistics import mean
import datetime
import re
import sys

# ---------- PDF (reportlab) ----------
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
except ImportError:
    # We’ll handle this in runtime by showing a friendly message if user tries to export PDF
    pass


DEFAULT_CATEGORIES = [
    "Subject Knowledge",
    "Communication",
    "Punctuality",
    "Teaching Style",
    "Student Engagement",
    "Assessment Fairness",
]


def clamp_rating(value: float) -> float:
    """Clamp rating to [1, 5]."""
    return max(1.0, min(5.0, value))


def stars_from_rating(avg: float, max_stars: int = 5) -> str:
    """
    Convert a numeric rating (0-5) to star string like ★★★★☆.
    We round to nearest half-star and render halves as '☆' + note. To avoid font issues,
    we stick to full stars by rounding to nearest integer for the star visuals,
    while still showing the numeric value separately.
    """
    # Visual stars: nearest integer (robust display)
    filled = int(round(avg))
    empty = max_stars - filled
    return "★" * filled + "☆" * empty


@dataclass
class FeedbackData:
    faculty_name: str
    categories: List[str] = field(default_factory=lambda: list(DEFAULT_CATEGORIES))
    # list of per-student dicts: {category: rating}
    entries: List[Dict[str, float]] = field(default_factory=list)

    def add_entry(self, entry: Dict[str, float]) -> None:
        self.entries.append(entry)

    def category_averages(self) -> Dict[str, float]:
        avgs: Dict[str, float] = {}
        for c in self.categories:
            vals = [e[c] for e in self.entries if c in e]
            avgs[c] = round(mean(vals), 2) if vals else 0.0
        return avgs

    def overall_average(self) -> float:
        if not self.entries:
            return 0.0
        # overall: mean of all category averages
        avgs = list(self.category_averages().values())
        return round(mean(avgs), 2) if avgs else 0.0


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]+", "_", name).strip("_") or "faculty"


def generate_pdf_report(data: FeedbackData, filename: str) -> None:
    try:
        # ensure reportlab is available
        from reportlab.lib.pagesizes import A4  # noqa: F401 (re-import for runtime check)
    except Exception as e:
        raise RuntimeError(
            "PDF generation requires the 'reportlab' package. Install it via:\n"
            "    pip install reportlab\n"
        ) from e

    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=48, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    normal = styles["BodyText"]
    small = ParagraphStyle('small', parent=normal, fontSize=9, leading=12)

    story = []

    story.append(Paragraph("Faculty Feedback Report", title_style))
    story.append(Spacer(1, 12))

    meta = [
        f"<b>Faculty:</b> {data.faculty_name}",
        f"<b>Responses:</b> {len(data.entries)}",
        f"<b>Generated on:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    for line in meta:
        story.append(Paragraph(line, normal))
    story.append(Spacer(1, 12))

    # Table of category averages
    cat_avgs = data.category_averages()
    table_data = [["Category", "Average (1–5)"]]
    for c in data.categories:
        table_data.append([c, f"{cat_avgs[c]:.2f}"])

    tbl = Table(table_data, colWidths=[3.5*inch, 1.5*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    story.append(Paragraph("<b>Category-wise Averages</b>", normal))
    story.append(Spacer(1, 6))
    story.append(tbl)
    story.append(Spacer(1, 12))

    overall = data.overall_average()
    star_str = stars_from_rating(overall)

    story.append(Paragraph("<b>Overall Rating</b>", normal))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"{overall:.2f} / 5.00", styles["Heading2"]))
    # Show stars big
    story.append(Paragraph(f"<para alignment='left'><font size=26>{star_str}</font></para>", normal))
    story.append(Spacer(1, 12))

    # Optional note for low ratings
    if overall < 3.0:
        story.append(Paragraph(
            "<i>Note:</i> Overall rating is below 3. Consider reviewing feedback details and planning improvements.",
            small
        ))

    doc.build(story)


def prompt_float(question: str, min_val: float = 1.0, max_val: float = 5.0) -> float:
    while True:
        try:
            raw = input(question).strip()
            val = float(raw)
            if val < min_val or val > max_val:
                print(f"Please enter a value between {min_val} and {max_val}.")
                continue
            return val
        except ValueError:
            print("Please enter a valid number (e.g., 4 or 3.5).")


def run_interactive() -> Tuple[FeedbackData, str]:
    print("=== Faculty Feedback System (Console) ===")
    faculty = input("Enter Faculty Name: ").strip()
    if not faculty:
        faculty = "Unknown Faculty"

    # Optionally allow custom categories
    use_default = input("Use default categories? (Y/n): ").strip().lower() or "y"
    if use_default.startswith("n"):
        categories = []
        print("Enter categories one per line. Leave blank to finish.")
        while True:
            c = input(f"Category {len(categories)+1}: ").strip()
            if not c:
                break
            categories.append(c)
        if not categories:
            categories = list(DEFAULT_CATEGORIES)
    else:
        categories = list(DEFAULT_CATEGORIES)

    data = FeedbackData(faculty_name=faculty, categories=categories)

    # Number of students
    while True:
        try:
            n = int(input("How many students will provide feedback? ").strip())
            if n <= 0:
                print("Enter a positive integer.")
                continue
            break
        except ValueError:
            print("Please enter a valid integer.")

    print("\nEnter ratings on a scale of 1–5 (you can use decimals like 4.5).")
    for i in range(1, n+1):
        print(f"\n--- Student {i} ---")
        entry: Dict[str, float] = {}
        for c in categories:
            entry[c] = clamp_rating(prompt_float(f"{c}: "))
        data.add_entry(entry)

    overall = data.overall_average()
    print("\n=== Results ===")
    print(f"Faculty: {data.faculty_name}")
    print("Category averages:")
    for c, avg in data.category_averages().items():
        print(f"  - {c}: {avg:.2f}")
    print(f"Overall Average: {overall:.2f}/5.00")
    print(f"Stars: {stars_from_rating(overall)}")

    # Generate PDF
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = sanitize_filename(data.faculty_name)
    pdf_name = f"feedback_{safe_name}_{ts}.pdf"
    try:
        generate_pdf_report(data, pdf_name)
        print(f"\nPDF generated: {pdf_name}")
    except RuntimeError as e:
        print("\nCould not generate PDF:", e)
        pdf_name = ""

    return data, pdf_name


if __name__ == "__main__":
    try:
        run_interactive()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
