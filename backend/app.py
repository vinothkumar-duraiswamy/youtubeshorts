from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import tempfile
import subprocess
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ✅ Allow large uploads (500 MB)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
USERS_FILE = os.path.join(BASE_DIR, "users.json")

# =====================================================
# ✅ ROOT for Railway healthcheck
# =====================================================
@app.get("/")
def home():
    return "✅ Backend is running", 200


# =====================================================
# ✅ LOGIN
# =====================================================
@app.post("/api/login")
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    for user in users:
        if user["username"] == username and user["password"] == password:
            return jsonify({"success": True})

    return jsonify({"success": False}), 401


# =====================================================
# ✅ FRONTEND ROUTES
# =====================================================
@app.get("/login.html")
def serve_login():
    return send_from_directory(FRONTEND_DIR, "login.html")

@app.get("/app.html")
def serve_app():
    return send_from_directory(FRONTEND_DIR, "app.html")

@app.get("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# =====================================================
# ✅ VIDEO GENERATOR API
# =====================================================
@app.post("/api/generate_video")
def generate_video():
    try:
        poster = request.files.get("poster")
        bg_music = request.files.get("bg_music")
        voice_over = request.files.get("voice_over")

        if not poster:
            return jsonify({"error": "Poster is required"}), 400

        tmp = tempfile.mkdtemp()

        poster_path = os.path.join(tmp, "poster.png")
        poster.save(poster_path)

        bg_path = None
        voice_path = None

        if bg_music:
            bg_path = os.path.join(tmp, "bg.mp3")
            bg_music.save(bg_path)

        if voice_over:
            voice_path = os.path.join(tmp, "voice.mp3")
            voice_over.save(voice_path)

        duration = 25
        if voice_path:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                voice_path
            ]
            out = subprocess.check_output(cmd).decode().strip()
            duration = float(out)

        output_path = os.path.join(tmp, "final_video.mp4")

        # ✅ FFMPEG LOGIC
        if voice_path and bg_path:
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", poster_path,
                "-i", bg_path,
                "-i", voice_path,
                "-filter_complex",
                "[1:a]volume=0.3[a_bg]; [a_bg][2:a]amix=inputs=2[a_mix]",
                "-map", "0:v",
                "-map", "[a_mix]",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-t", str(duration),
                output_path
            ]

        elif voice_path:
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", poster_path,
                "-i", voice_path,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-t", str(duration),
                output_path
            ]

        elif bg_path:
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", poster_path,
                "-i", bg_path,
                "-filter_complex",
                "[1:a]volume=0.3[a_bg]",
                "-map", "0:v",
                "-map", "[a_bg]",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-t", "25",
                output_path
            ]

        else:
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", poster_path,
                "-t", "25",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                output_path
            ]

        subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# ✅ IMPORTANT FOR RAILWAY (Dynamic PORT)
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
