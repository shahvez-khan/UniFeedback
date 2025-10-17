import sqlite3
from contextlib import closing
from reportlab.lib.pagesizes import A4
# Replaced canvas with platypus imports for professional formatting
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

CATEGORIES = ["Knowledge", "Clarity", "Engagement", "Punctuality"]

def ensure_db(db_path):
    with closing(sqlite3.connect(db_path)) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty TEXT,
            student TEXT,
            ratings TEXT,
            comment TEXT
        )''')
        conn.commit()

def insert_submission(db_path, faculty, student, ratings, comment):
    with closing(sqlite3.connect(db_path)) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO feedback (faculty, student, ratings, comment) VALUES (?,?,?,?)",
                  (faculty, student, str(ratings), comment))
        conn.commit()

def get_faculties(db_path):
    with closing(sqlite3.connect(db_path)) as conn:
        c = conn.cursor()
        c.execute("SELECT DISTINCT faculty FROM feedback")
        return [row[0] for row in c.fetchall()]

# MODIFIED: Now returns response_count and overall_average
def get_faculty_summary(db_path, faculty):
    with closing(sqlite3.connect(db_path)) as conn:
        c = conn.cursor()
        c.execute("SELECT ratings, comment FROM feedback WHERE faculty=?", (faculty,))
        rows = c.fetchall()
        if not rows:
            return None
        
        response_count = len(rows)
        
        totals = {cat: 0 for cat in CATEGORIES}
        counts = {cat: 0 for cat in CATEGORIES}
        comments = []
        
        for ratings_str, comment in rows:
            try:
                # Retain original use of eval() for compatibility with the database structure
                ratings = eval(ratings_str) 
            except:
                continue
            
            for cat in CATEGORIES:
                if cat in ratings:
                    totals[cat] += ratings[cat]
                    counts[cat] += 1
            if comment:
                comments.append(comment)
        
        # Calculate category averages
        averages = {cat: round(totals[cat]/counts[cat],2) if counts[cat]>0 else 0.0 for cat in CATEGORIES}
        
        # Calculate overall average (mean of all category averages)
        overall_avg = round(sum(averages.values()) / len(CATEGORIES), 2) if CATEGORIES else 0.0

        return {
            "averages": averages, 
            "comments": comments,
            "response_count": response_count,
            "overall_average": overall_avg
        }

# NEW: Utility function for star display in PDF
def stars_from_rating(avg: float, max_stars: int = 5) -> str:
    filled = int(round(avg))
    empty = max_stars - filled
    return "★" * filled + "☆" * empty

# MODIFIED: Generates a professional PDF report
def build_pdf_for_faculty(db_path, faculty, buffer):
    summary = get_faculty_summary(db_path, faculty)
    
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading2_style = styles["Heading2"]
    normal = styles["BodyText"]
    
    story = []

    story.append(Paragraph("Faculty Feedback Report", title_style))
    story.append(Spacer(1, 18))

    if not summary:
        story.append(Paragraph(f"No feedback available for {faculty}.", normal))
        doc.build(story)
        return

    # Metadata
    meta = [
        f"<b>Faculty Member:</b> {faculty}",
        f"<b>Total Responses:</b> {summary['response_count']}",
        f"<b>Overall Rating:</b> {summary['overall_average']:.2f} / 5.00",
    ]
    for line in meta:
        story.append(Paragraph(line, normal))
    story.append(Spacer(1, 18))

    # Overall Star Rating 
    star_str = stars_from_rating(summary['overall_average'])
    story.append(Paragraph("<b>Overall Star Rating</b>", heading2_style))
    story.append(Spacer(1, 6))
    star_paragraph = Paragraph(f"<para alignment='left'><font size=30 color='rgb(255,191,0)'>{star_str}</font></para>", normal)
    story.append(star_paragraph)
    story.append(Spacer(1, 18))

    # Table of category averages
    cat_avgs = summary['averages']
    table_data = [["Category", "Average (1–5)"]]
    for c in CATEGORIES:
        table_data.append([c, f"{cat_avgs.get(c, 0.0):.2f}"])

    tbl = Table(table_data, colWidths=[3.5*inch, 1.5*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor('#0056b3')), 
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("ALIGN", (1,0), (-1,-1), "CENTER"), 
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))

    story.append(Paragraph("<b>Category-wise Averages</b>", heading2_style))
    story.append(Spacer(1, 6))
    story.append(tbl)
    story.append(Spacer(1, 18))
    
    # Comments Section
    story.append(Paragraph("<b>Student Comments</b>", heading2_style))
    story.append(Spacer(1, 6))
    
    if summary["comments"]:
        for com in summary["comments"]:
            story.append(Paragraph(f"• {com}", normal))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No specific comments were provided.", normal))
        
    doc.build(story)