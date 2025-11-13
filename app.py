from flask import Flask, render_template_string, request, send_from_directory
import os
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Folder to save reports
UPLOAD_FOLDER = "reports"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Excel file to store report data
EXCEL_FILE = os.path.join(UPLOAD_FOLDER, "reports.xlsx")

# Initialize Excel file if not exists
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["Engineer Name", "Date", "Time", "Audio File"])
    df.to_excel(EXCEL_FILE, index=False)

# ---------------- MAIN PAGE ----------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Engineer Report</title>
<style>
  body { font-family: Arial; margin: 40px; text-align: center; background: #f0f4f8; }
  h2 { color: #007BFF; }
  input, button { margin: 10px; padding: 10px; font-size: 16px; border-radius: 8px; border: 1px solid #ccc; }
  button { background-color: #007BFF; color: white; cursor: pointer; }
  button:hover { background-color: #0056b3; }
</style>
</head>
<body>
  <h2>🎙 Engineer Voice Report</h2>
  <form id="reportForm" method="POST" enctype="multipart/form-data">
    <input type="text" name="engineer" placeholder="Enter Engineer Name" required><br>
    <button type="button" onclick="startRecording()">Start Recording</button>
    <button type="button" onclick="stopRecording()">Stop Recording</button><br>
    <audio id="audioPlayer" controls></audio><br>
    <input type="hidden" name="audio" id="audioData">
    <button type="submit">Submit Report</button>
  </form>
  <p><a href="/reports">📂 View All Reports</a></p>
  
<script>
let mediaRecorder;
let audioChunks = [];

async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();

    audioChunks = [];
    mediaRecorder.addEventListener("dataavailable", event => {
        audioChunks.push(event.data);
    });
}

async function stopRecording() {
    mediaRecorder.stop();
    mediaRecorder.addEventListener("stop", () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
            document.getElementById("audioData").value = reader.result;
            document.getElementById("audioPlayer").src = reader.result;
        };
    });
}
</script>
</body>
</html>
"""

# ---------------- ROUTES ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        engineer = request.form["engineer"]
        audio_data = request.form["audio"]

        # Decode and save the audio file
        if audio_data.startswith("data:audio/wav;base64,"):
            audio_data = audio_data.split(",")[1]
        import base64
        audio_bytes = base64.b64decode(audio_data)

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")

        filename = secure_filename(f"{engineer}_{date_str}_{time_str}.wav")
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as f:
            f.write(audio_bytes)

        # Save record in Excel
        df = pd.read_excel(EXCEL_FILE)
        new_row = {"Engineer Name": engineer, "Date": date_str, "Time": time_str, "Audio File": filename}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)

        return "✅ Report Saved Successfully!<br><a href='/'>Back</a> | <a href='/reports'>View Reports</a>"

    return render_template_string(HTML_PAGE)

# ---------------- REPORTS PAGE ----------------
@app.route("/reports")
def list_reports():
    df = pd.read_excel(EXCEL_FILE)
    table_html = df.to_html(index=False, justify="center", border=1)

    files = os.listdir(UPLOAD_FOLDER)
    audio_links = [
        f"<li><a href='/download/{file}'>{file}</a></li>"
        for file in files if file.endswith(".wav")
    ]
    page = f"""
    <html>
    <head><title>Reports Dashboard</title></head>
    <body style='font-family: Arial; background: #f0f4f8; text-align:center;'>
      <h2>📊 Reports Dashboard</h2>
      <p><a href="/">⬅️ Back to Home</a></p>
      <h3>Excel Report:</h3>
      <a href="/download/reports.xlsx">📁 Download Excel File</a>
      <h3>Audio Reports:</h3>
      <ul style='list-style:none;'>{''.join(audio_links)}</ul>
      <h3>Data Summary:</h3>
      {table_html}
    </body>
    </html>
    """
    return page

# ---------------- DOWNLOAD ----------------
@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
