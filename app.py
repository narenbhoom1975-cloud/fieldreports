from flask import Flask, render_template_string, request, redirect, send_from_directory
from openpyxl import Workbook, load_workbook
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
EXCEL_FILE = "reports.xlsx"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create Excel file if not exists
if not os.path.exists(EXCEL_FILE):
    wb = Workbook()
    ws = wb.active
    ws.append(["Date", "Engineer Name", "Client Name", "Problem", "Solution", "Voice File"])
    wb.save(EXCEL_FILE)

# HTML Form
HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Field Report</title>
</head>
<body>
  <h2>Engineer Field Report</h2>
  <form action="/submit" method="post" enctype="multipart/form-data">
    Engineer Name: <input type="text" name="engineer"><br><br>
    Client Name: <input type="text" name="client"><br><br>
    Problem: <input type="text" name="problem"><br><br>
    Solution: <input type="text" name="solution"><br><br>
    Voice Report: <input type="file" name="voice" accept="audio/*" capture="microphone"><br><br>
    <button type="submit">Submit Report</button>
  </form>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/submit", methods=["POST"])
def submit():
    engineer = request.form["engineer"]
    client = request.form["client"]
    problem = request.form["problem"]
    solution = request.form["solution"]

    # Save voice file
    voice = request.files["voice"]
    filename = f"{engineer}_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.mp3"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    voice.save(file_path)

    # Save details to Excel
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    ws.append([datetime.now().strftime("%d-%m-%Y %H:%M"), engineer, client, problem, solution, filename])
    wb.save(EXCEL_FILE)

    return "<h3>✅ Report Submitted Successfully!</h3><a href='/'>Back</a>"

@app.route("/uploads/<path:filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
