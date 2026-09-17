from flask import Flask, render_template, request
import google.generativeai as genai
import sqlite3
from flask import send_file
import io
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Gemini API
genai.configure(api_key="YOUR_API_KEY")

model = genai.GenerativeModel(
    "gemini-3.6-flash"
)

# --------------------
# Database Setup
# --------------------

def init_db():

    conn = sqlite3.connect("travel.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS trips(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination TEXT,
        days TEXT,
        budget TEXT,
        itinerary TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()

# --------------------
# Home
# --------------------

@app.route("/")
def home():

    return render_template(
        "index.html"
    )

@app.route("/download_pdf", methods=["POST"])
def download_pdf():

    content = request.form["content"]

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer)

    y = 800

    for line in content.split("\n"):

        pdf.drawString(40, y, line[:100])

        y -= 20

        if y < 40:
            pdf.showPage()
            y = 800

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="travel_guide.pdf",
        mimetype="application/pdf"
    )

# --------------------
# Generate Travel Plan
# --------------------

@app.route("/plan", methods=["POST"])
def plan():

    destination = request.form["destination"]
    days = request.form["days"]
    budget = request.form["budget"]

    prompt = f"""
Create a travel guide.

Destination: {destination}
Days: {days}
Budget: {budget}

Rules:
- No markdown
- No # symbols
- No ***
- No ---
- Use clean plain text

Generate:

1. Day-wise itinerary

2. Recommended hotels

3. Recommended food

4. Best time to visit

5. Estimated budget
"""

    response = model.generate_content(
        prompt
    )

    itinerary = response.text

    # Save trip

    conn = sqlite3.connect("travel.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO trips
    (destination, days, budget, itinerary)
    VALUES (?, ?, ?, ?)
    """,
    (
        destination,
        days,
        budget,
        itinerary
    ))

    conn.commit()
    conn.close()

    # Temporary image
    image_url = "https://images.unsplash.com/photo-1502602898657-3e91760cbb34"

    return render_template(
        "index.html",
        itinerary=itinerary,
        destination=destination,
        image_url=image_url
    )

# --------------------
# Travel History
# --------------------

@app.route("/history")
def history():

    conn = sqlite3.connect("travel.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM trips
    ORDER BY id DESC
    """)

    trips = cur.fetchall()

    conn.close()

    return render_template(
        "history.html",
        trips=trips
    )

# --------------------
# Run App
# --------------------

if __name__ == "__main__":
    app.run(debug=True)