import os
import uuid
import subprocess
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ✅ -------- Helper to save uploaded files --------
def save_file(file):
    if not file:
        return None
    
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)
    return filepath


# ✅ -------- LOGIN API --------
@app.route("/api/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "admin":
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})


# ✅ -------- Generate Video API --------
@app.route("/api/generate_video", methods=["POST"])
def generate_video():
    print("✅ Received /api/generate_video request")

    poster = request.files.get("poster")
    bg_music = request.files.get("bg_music")
    voice_over = request.files.get("voice_over")

    if not poster:
        return jsonify({"error": "Poster image missing"}), 400
    if not bg_music:
        return jsonify({"error": "Background audio missing"}), 400

    poster_path = save_file(poster)
    bg_path = save_file(bg_music)
    voice_path = save_file(voice_over) if voice_over else None

    final_path = f"/app/uploads/final_{uuid.uuid4().hex}.mp4"

    # ✅ Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", poster_path,
        "-t", "15",
        "-i", bg_path
    ]

    if voice_path:
        cmd.extend(["-i", voice_path])

    cmd.extend([
        "-map", "0:v",
        "-map", "1:a",
        "-vf", "scale=1080:1920",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "28",
        final_path
    ])

    print("✅ Running FFmpeg command:")
    print(" ".join(cmd))

    # ✅ RUN FFmpeg (non-blocking)
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # ✅ WAIT for completion
    stdout, stderr = process.communicate()
    print("✅ FFmpeg Completed")
    print(stderr.decode())

    # ✅ Return final video
    return send_file(final_path, as_attachment=True, download_name="final_video.mp4")


@app.route("/")
def home():
    return "✅ Backend is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
