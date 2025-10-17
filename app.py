from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import sqlite3
from contextlib import closing
from io import BytesIO
import os
from feedback_logic import (
    CATEGORIES,
    ensure_db,
    insert_submission,
    get_faculties,
    get_faculty_summary,
    build_pdf_for_faculty,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")

DB_PATH = os.environ.get("DATABASE_URL", "feedback.db")
ensure_db(DB_PATH)

@app.get("/")
def home():
    return render_template("home.html")

@app.get("/feedback")
def feedback():
    return render_template("feedback.html", categories=CATEGORIES)

@app.post("/submit")
def submit():
    faculty = request.form.get("faculty", "").strip()
    student = request.form.get("student", "").strip()
    comment = request.form.get("comment", "").strip()
    ratings = {}
    
    # IMPROVED VALIDATION
    if not faculty:
        flash("Faculty name is required.", "error")
        return redirect(url_for("feedback"))

    all_ratings_valid = True
    for cat in CATEGORIES:
        val = request.form.get(f"rating_{cat}", "")
        try:
            num = int(val)
        except ValueError:
            num = 0
        
        if num < 1 or num > 5:
            all_ratings_valid = False
            
        ratings[cat] = num
        
    if not all_ratings_valid:
        # Better feedback to the user on missing ratings
        flash("Please provide a rating (1-5) for all categories.", "error")
        return redirect(url_for("feedback"))

    insert_submission(DB_PATH, faculty, student, ratings, comment)
    flash("Feedback submitted successfully!", "success")
    return redirect(url_for("results", faculty=faculty))

@app.get("/results")
def results():
    faculty = request.args.get("faculty", "").strip()
    faculties = get_faculties(DB_PATH)
    summary = None
    if faculty:
        # get_faculty_summary now returns response_count and overall_average
        summary = get_faculty_summary(DB_PATH, faculty)
    return render_template("results.html", faculties=faculties, selected_faculty=faculty, summary=summary, categories=CATEGORIES)

@app.get("/report/<path:faculty>.pdf")
def report_pdf(faculty):
    buffer = BytesIO()
    # build_pdf_for_faculty now uses the professional report format
    build_pdf_for_faculty(DB_PATH, faculty, buffer)
    buffer.seek(0)
    filename = f"{faculty.replace(' ', '_')}_feedback_report.pdf"
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)

if __name__ == "__main__":
    app.run(debug=True)
