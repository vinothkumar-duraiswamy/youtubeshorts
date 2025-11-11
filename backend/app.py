from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import tempfile
import subprocess
import json

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
USERS_FILE = os.path.join(BASE_DIR, "users.json")

# -----------------------------
# ✅ ROOT (Health Check)
# -----------------------------
@app.get("/")
def home():
    return "Backend running ✅", 200


# -----------------------------
# ✅ LOGIN
# -----------------------------
@app.post("/api/login")
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    for u in users:
        if u["username"] == username and u["password"] == password:
            return jsonify({"success": True})

    return jsonify({"success": False}), 401


# -----------------------------
# ✅ VIDEO GENERATION
# -----------------------------
@app.post("/api/generate_video")
def generate_video():
    try:
        poster = request.files.get("poster")
        bg_music = request.files.get("bg_music")
        voice = request.files.get("voice_over")

        if not poster:
            return jsonify({"error": "Poster required"}), 400

        tmp = tempfile.mkdtemp()

        poster_path = os.path.join(tmp, "poster.png")
        poster.save(poster_path)

        bg_path = None
        voice_path = None

        if bg_music:
            bg_path = os.path.join(tmp, "bg.mp3")
            bg_music.save(bg_path)

        if voice:
            voice_path = os.path.join(tmp, "voice.mp3")
            voice.save(voice_path)

        # -----------------------------
        # ✅ Get duration from voice (if any)
        # -----------------------------
        duration = 25
        if voice_path:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                voice_path
            ]
            out = subprocess.check_output(cmd).decode().strip()
            duration = float(out)

        output_path = os.path.join(tmp, "output.mp4")

        # -----------------------------
        # ✅ FFmpeg command
        # -----------------------------
        if bg_path and voice_path:
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", poster_path,
                "-i", bg_path,
                "-i", voice_path,
                "-filter_complex",
                "[1:a]volume=0.3[a1];[a1][2:a]amix=inputs=2[aout]",
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "libx264",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                output_path
            ]

        elif voice_path:
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", poster_path,
                "-i", voice_path,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "libx264",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                output_path
            ]

        elif bg_path:
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", poster_path,
                "-i", bg_path,
                "-filter_complex", "[1:a]volume=0.4[aout]",
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "libx264",
                "-t", "25",
                "-pix_fmt", "yuv420p",
                output_path
            ]

        else:
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", poster_path,
                "-t", "25",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                output_path
            ]

        print("✅ Running FFmpeg:")
        print(" ".join(cmd))

        subprocess.run(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 2000:
            return jsonify({"error": "FFmpeg failed! File too small."}), 500

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# -----------------------------
# ✅ RUN
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
