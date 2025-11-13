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
  return """
<h2>Engineer Voice Report</h2>

<label>Engineer Name:</label><br>
<input id="name" required><br><br>

<label>Record Voice:</label><br>

<button onclick="startRecording()">🎙 Start Recording</button>
<button onclick="stopRecording()" disabled id="stopBtn">⏹ Stop Recording</button>

<p id="status"></p>

<form id="reportForm" method="POST" action="/submit" enctype="multipart/form-data" style="display:none;">
    <input type="hidden" name="name" id="hiddenName">
    <input type="file" name="audio" id="audioFile">
</form>

<script>
let mediaRecorder;
let audioChunks = [];

async function startRecording() {
    document.getElementById("status").innerHTML = "Recording...";
    document.getElementById("stopBtn").disabled = false;

    let stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.start();
    audioChunks = [];

    mediaRecorder.ondataavailable = e => {
        audioChunks.push(e.data);
    };
}

function stopRecording() {
    mediaRecorder.stop();
    document.getElementById("status").innerHTML = "Processing...";

    mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunks, { type: "audio/mp3" });
        const file = new File([blob], "recording.mp3");

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);

        document.getElementById("audioFile").files = dataTransfer.files;

        // set name
        document.getElementById("hiddenName").value = document.getElementById("name").value;

        // submit form automatically
        document.getElementById("reportForm").submit();
    };
}
</script>
"""

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
