from flask import Flask, request, send_from_directory, redirect, make_response
from openpyxl import Workbook, load_workbook
import os
import datetime
from zipfile import ZipFile

app = Flask(__name__)

ADMIN_PASSWORD = "password123"

# Create storage folders
if not os.path.exists("voice_reports"):
    os.makedirs("voice_reports")

# Create Excel file if missing
if not os.path.exists("reports.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.append(["Engineer", "Date", "Audio File"])
    wb.save("reports.xlsx")


@app.route("/")
def home():
    return """
    <h2>Engineer Voice Report</h2>
    <form method="POST" action="/submit" enctype="multipart/form-data">
        <label>Engineer Name:</label><br>
        <input name="name" required><br><br>

        <label>Record Voice:</label><br>
        <input type="file" name="audio" accept="audio/*" required><br><br>

        <button type="submit">Submit Report</button>
    </form>
    """


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    audio = request.files.get("audio")

    if audio:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.mp3"
        filepath = os.path.join("voice_reports", filename)
        audio.save(filepath)

        # Save to Excel
        wb = load_workbook("reports.xlsx")
        ws = wb.active
        ws.append([name, timestamp, filename])
        wb.save("reports.xlsx")

    return "<h3>Report submitted successfully!</h3>"


# -------- ADMIN PROTECTION --------

def admin_protected(request):
    pwd = request.cookies.get("admin_pass")
    return pwd == ADMIN_PASSWORD


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return """
        <h2>Admin Login</h2>
        <form method="POST">
            <input name="password" type="password" placeholder="Enter Password">
            <button type="submit">Login</button>
        </form>
        """

    password = request.form.get("password")

    if password == ADMIN_PASSWORD:
        resp = make_response(redirect("/admin"))
        resp.set_cookie("admin_pass", ADMIN_PASSWORD)
        return resp
    else:
        return "<h3>Wrong Password</h3>"


@app.route("/admin")
def admin():
    if not admin_protected(request):
        return redirect("/admin_login")

    files = os.listdir("voice_reports")

    page = """
    <h2>Admin Panel</h2>
    <a href='/download_excel'>📄 Download Excel Report</a><br><br>
    <a href='/download_all_audio'>🎧 Download All Audio (ZIP)</a><br><br>
    <h3>Individual Audio Files:</h3>
    """

    for f in files:
        page += f"<a href='/audio/{f}' download>{f}</a><br>"

    return page


@app.route("/download_excel")
def download_excel():
    if not admin_protected(request):
        return redirect("/admin_login")
    return send_from_directory(".", "reports.xlsx", as_attachment=True)


@app.route("/audio/<filename>")
def download_audio(filename):
    if not admin_protected(request):
        return redirect("/admin_login")
    return send_from_directory("voice_reports", filename, as_attachment=True)


@app.route("/download_all_audio")
def download_all_audio():
    if not admin_protected(request):
        return redirect("/admin_login")

    zip_path = "all_audio.zip"
    with ZipFile(zip_path, "w") as zipf:
        for file in os.listdir("voice_reports"):
            zipf.write(os.path.join("voice_reports", file), file)

    return send_from_directory(".", zip_path, as_attachment=True)


# -------- PORT FOR RENDER --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
