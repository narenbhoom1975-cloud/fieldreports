from flask import Flask, request, send_from_directory, redirect, make_response
from openpyxl import Workbook, load_workbook
import os
import datetime
from zipfile import ZipFile
from pydub import AudioSegment

app = Flask(__name__)
ADMIN_PASSWORD = "password123"

# Create storage folders
if not os.path.exists("voice_reports"):
    os.makedirs("voice_reports")

if not os.path.exists("temp_uploads"):
    os.makedirs("temp_uploads")

# Create Excel file if missing
if not os.path.exists("reports.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.append(["Engineer", "Date", "Audio File"])
    wb.save("reports.xlsx")

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Engineer Voice Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            button { padding: 10px 20px; margin: 5px; font-size: 16px; cursor: pointer; }
            button:disabled { opacity: 0.5; cursor: not-allowed; }
            input[type="text"] { padding: 8px; width: 300px; font-size: 14px; }
            #status { color: #007bff; font-weight: bold; margin-top: 10px; }
            .recording { color: #dc3545; }
        </style>
    </head>
    <body>
        <h2>Engineer Voice Report</h2>
        <label>Engineer Name:</label><br>
        <input type="text" id="name" required><br><br>
        
        <label>Record Voice:</label><br>
        <button onclick="startRecording()" id="startBtn">🎙 Start Recording</button>
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
            const nameInput = document.getElementById("name");
            if (!nameInput.value.trim()) {
                alert("Please enter your name first!");
                return;
            }
            
            try {
                document.getElementById("startBtn").disabled = true;
                document.getElementById("stopBtn").disabled = false;
                document.getElementById("status").innerHTML = "🔴 Recording...";
                document.getElementById("status").className = "recording";
                
                // Request audio with specific constraints
                let stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 44100
                    } 
                });
                
                // Try to use audio/webm;codecs=opus or fallback to default
                let mimeType = 'audio/webm;codecs=opus';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/webm';
                }
                
                mediaRecorder = new MediaRecorder(stream, {
                    mimeType: mimeType,
                    audioBitsPerSecond: 128000
                });
                
                audioChunks = [];
                
                mediaRecorder.ondataavailable = e => {
                    if (e.data.size > 0) {
                        audioChunks.push(e.data);
                    }
                };
                
                mediaRecorder.start();
                
            } catch (err) {
                document.getElementById("status").innerHTML = "❌ Error: " + err.message;
                document.getElementById("startBtn").disabled = false;
                document.getElementById("stopBtn").disabled = true;
                console.error(err);
            }
        }
        
        function stopRecording() {
            if (!mediaRecorder || mediaRecorder.state === 'inactive') return;
            
            mediaRecorder.stop();
            document.getElementById("status").innerHTML = "⏳ Processing and converting to MP3...";
            document.getElementById("stopBtn").disabled = true;
            
            mediaRecorder.onstop = async () => {
                // Stop all audio tracks
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                
                // Create blob from recorded chunks
                const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
                
                console.log("Recorded blob size:", blob.size, "bytes");
                
                if (blob.size === 0) {
                    document.getElementById("status").innerHTML = "❌ Error: Recording is empty. Please try again.";
                    document.getElementById("startBtn").disabled = false;
                    return;
                }
                
                const file = new File([blob], "recording.webm", { type: mediaRecorder.mimeType });
                
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                document.getElementById("audioFile").files = dataTransfer.files;
                
                // Set name
                document.getElementById("hiddenName").value = document.getElementById("name").value;
                
                // Submit form automatically
                document.getElementById("reportForm").submit();
            };
        }
        </script>
    </body>
    </html>
    """

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    audio = request.files.get("audio")
    
    if audio and name:
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save temporary webm file
            temp_webm = os.path.join("temp_uploads", f"temp_{timestamp}.webm")
            audio.save(temp_webm)
            
            # Convert to MP3
            final_mp3 = os.path.join("voice_reports", f"{name}_{timestamp}.mp3")
            
            # Load audio and convert to MP3
            audio_segment = AudioSegment.from_file(temp_webm, format="webm")
            audio_segment.export(final_mp3, format="mp3", bitrate="128k")
            
            # Remove temporary file
            os.remove(temp_webm)
            
            # Save to Excel
            wb = load_workbook("reports.xlsx")
            ws = wb.active
            date_formatted = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws.append([name, date_formatted, f"{name}_{timestamp}.mp3"])
            wb.save("reports.xlsx")
            
            return """
            <html>
            <head>
                <meta http-equiv="refresh" content="2;url=/" />
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
                </style>
            </head>
            <body>
                <h3>✅ Report submitted successfully!</h3>
                <p>Your voice recording has been converted to MP3 format.</p>
                <p>Redirecting back to home page...</p>
                <a href="/">Submit another report</a>
            </body>
            </html>
            """
        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            return f"<h3>❌ Error processing audio: {str(e)}</h3><a href='/'>Go back</a>"
    else:
        return "<h3>❌ Error: Missing name or audio file</h3><a href='/'>Go back</a>"

# -------- ADMIN PROTECTION --------
def admin_protected(request):
    pwd = request.cookies.get("admin_pass")
    return pwd == ADMIN_PASSWORD

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                input { padding: 10px; font-size: 14px; }
                button { padding: 10px 20px; font-size: 14px; cursor: pointer; }
            </style>
        </head>
        <body>
            <h2>Admin Login</h2>
            <form method="POST">
                <input name="password" type="password" placeholder="Enter Password" required>
                <button type="submit">Login</button>
            </form>
        </body>
        </html>
        """
    
    password = request.form.get("password")
    if password == ADMIN_PASSWORD:
        resp = make_response(redirect("/admin"))
        resp.set_cookie("admin_pass", ADMIN_PASSWORD)
        return resp
    else:
        return "<h3>❌ Wrong Password</h3><a href='/admin_login'>Try again</a>"

@app.route("/admin")
def admin():
    if not admin_protected(request):
        return redirect("/admin_login")
    
    files = sorted(os.listdir("voice_reports"), reverse=True)
    
    page = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            a { text-decoration: none; color: #007bff; }
            a:hover { text-decoration: underline; }
            .file-list { margin-top: 20px; }
            .file-item { padding: 8px; border-bottom: 1px solid #eee; }
            .logout { float: right; color: #dc3545; }
        </style>
    </head>
    <body>
        <h2>Admin Panel <a href='/admin_logout' class='logout'>Logout</a></h2>
        <p>
            <a href='/download_excel'>📄 Download Excel Report</a><br><br>
            <a href='/download_all_audio'>🎧 Download All Audio (ZIP)</a><br><br>
        </p>
        
        <h3>Individual Audio Files (""" + str(len(files)) + """ MP3 files):</h3>
        <div class="file-list">
    """
    
    for f in files:
        page += f"<div class='file-item'><a href='/audio/{f}' download>🎵 {f}</a></div>"
    
    page += """
        </div>
    </body>
    </html>
    """
    
    return page

@app.route("/admin_logout")
def admin_logout():
    resp = make_response(redirect("/admin_login"))
    resp.set_cookie("admin_pass", "", expires=0)
    return resp

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
    app.run(host="0.0.0.0", port=10000, debug=False)
