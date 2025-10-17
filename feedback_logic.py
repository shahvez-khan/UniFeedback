import os
import json
# NEW: Import SQLAlchemy components to handle flexible database connections
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
# Removed: import sqlite3

# Reportlab imports remain the same
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

CATEGORIES = ["Knowledge", "Clarity", "Engagement", "Punctuality"]

# --- NEW: SQLAlchemy Global Engine and Connection Manager ---
ENGINE = None
def get_engine(db_path):
    """Initializes the SQLAlchemy Engine, handling PostgreSQL URL formatting."""
    global ENGINE
    if ENGINE is not None:
        return ENGINE
    
    # Convert 'postgres://' (used by Heroku/Render) to 'postgresql://' (used by SQLAlchemy)
    if db_path and db_path.startswith("postgres://"):
        db_path = db_path.replace("postgres://", "postgresql://", 1)
    
    # For local SQLite, use check_same_thread=False to prevent concurrency issues with Flask
    connect_args = {"check_same_thread": False} if db_path.startswith("sqlite") else {}
    
    ENGINE = create_engine(db_path, connect_args=connect_args)
    return ENGINE

@contextmanager
def db_session(db_path):
    """Provides a context-managed database connection with transaction handling."""
    conn = None
    trans = None
    try:
        engine = get_engine(db_path)
        conn = engine.connect()
        trans = conn.begin()
        yield conn
        trans.commit()
    except SQLAlchemyError:
        if trans:
            trans.rollback()
        raise
    finally:
        if conn:
            conn.close()

# MODIFIED: Uses SQLAlchemy to create the table
def ensure_db(db_path):
    engine = get_engine(db_path)
    # Use SERIAL PRIMARY KEY for Postgres compatibility; INTEGER PRIMARY KEY for SQLite
    if db_path.startswith("postgresql"):
        pk_type = "SERIAL PRIMARY KEY"
    else:
        pk_type = "INTEGER PRIMARY KEY"

    create_table_sql = text(f'''CREATE TABLE IF NOT EXISTS feedback (
        id {pk_type},
        faculty TEXT,
        student TEXT,
        ratings TEXT,
        comment TEXT
    )''')
    
    try:
        with engine.connect() as conn:
            conn.execute(create_table_sql)
            conn.commit()
    except SQLAlchemyError as e:
        # Log error during table creation, but don't stop the app
        print(f"Error ensuring DB table: {e}")

# MODIFIED: Uses SQLAlchemy text() for secure parameter passing
def insert_submission(db_path, faculty, student, ratings, comment):
    with db_session(db_path) as conn:
        insert_sql = text("INSERT INTO feedback (faculty, student, ratings, comment) VALUES (:faculty, :student, :ratings, :comment)")
        conn.execute(insert_sql, {
            "faculty": faculty, 
            "student": student, 
            "ratings": str(ratings), 
            "comment": comment
        })

# MODIFIED: Uses SQLAlchemy for fetching distinct faculties
def get_faculties(db_path):
    with db_session(db_path) as conn:
        select_sql = text("SELECT DISTINCT faculty FROM feedback")
        # .scalars().all() fetches a list of the first column value (faculty name)
        result = conn.execute(select_sql).scalars().all()
        return list(result)

# MODIFIED: Uses SQLAlchemy for fetching data for summary
def get_faculty_summary(db_path, faculty):
    # This function uses the old raw logic after fetching data
    with db_session(db_path) as conn:
        select_sql = text("SELECT ratings, comment FROM feedback WHERE faculty=:faculty")
        # .fetchall() returns a list of tuples like the old sqlite3 result
        rows = conn.execute(select_sql, {"faculty": faculty}).fetchall()

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

# Remaining PDF functions are unchanged as they rely only on the summary dict
def stars_from_rating(avg: float, max_stars: int = 5) -> str:
    filled = int(round(avg))
    empty = max_stars - filled
    return "★" * filled + "☆" * empty

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
