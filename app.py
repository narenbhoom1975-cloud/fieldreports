from flask import Flask, render_template_string, request, send_from_directory
import os
from datetime import datetime

app = Flask(__name__)

# Folder to save reports
UPLOAD_FOLDER = "reports"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# HTML Page
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Engineer Report</title>
  <style>
    body { font-family: Arial; background: #eef2f3; text-align: center; padding: 20px; }
    h1 { color: #333; }
    input, textarea, button { width: 90%; max-width: 400px; padding: 10px; margin: 8px; border-radius: 6px; border: 1px solid #ccc; }
    button { background-color: #007bff; color: white; border: none; font-size: 16px; cursor: pointer; }
    button:hover { background-color: #0056b3; }
    audio { margin-top: 10px; }
  </style>
</head>
<body>
  <h1>Engineer Field Report</h1>
  <form id="reportForm" enctype="multipart/form-data" method="POST" action="/submit">
    <input name="engineer" placeholder="Engineer Name" required><br>
    <input name="client" placeholder="Client Name" required><br>
    <textarea name="problem" placeholder="Describe problem & solution" rows="4" required></textarea><br>
    
    <button type="button" onclick="startRecording()">🎙 Start Recording</button>
    <button type="button" onclick="stopRecording()">⏹ Stop Recording</button><br>
    <audio id="player" controls></audio><br>
    
    <input type="hidden" name="audio_filename" id="audio_filename">
    <button type="submit">📤 Submit Report</button>
  </form>

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

      alert("🎙 Recording started...");
    }

    function stopRecording() {
      mediaRecorder.stop();
      mediaRecorder.addEventListener("stop", () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
        const audioUrl = URL.createObjectURL(audioBlob);
        document.getElementById("player").src = audioUrl;

        const filename = "audio_" + Date.now() + ".mp3";
        const formData = new FormData();
        formData.append("audio_data", audioBlob, filename);

        fetch("/upload_audio", { method: "POST", body: formData })
          .then(response => response.text())
          .then(data => {
            document.getElementById("audio_filename").value = data;
            alert("✅ Audio saved successfully!");
          });
      });
    }
  </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    audio = request.files['audio_data']
    filename = audio.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio.save(filepath)
    return filename

@app.route('/submit', methods=['POST'])
def submit():
    engineer = request.form['engineer']
    client = request.form['client']
    problem = request.form['problem']
    audio_filename = request.form['audio_filename']
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Save report as text
    report_text = f"Engineer: {engineer}\nClient: {client}\nProblem: {problem}\nAudio: {audio_filename}\nDate: {date}\n{'-'*40}\n"
    with open(os.path.join(UPLOAD_FOLDER, "reports.txt"), "a", encoding="utf-8") as f:
        f.write(report_text)

    return f"<h2>✅ Report saved!</h2><p>Engineer: {engineer}<br>Client: {client}<br>Date: {date}</p><a href='/'>Go back</a>"

@app.route('/reports/<path:filename>')
def serve_audio(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    # Make it visible on your mobile too
    app.run(host="0.0.0.0", port=5000, debug=True)
