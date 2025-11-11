import os
import tempfile
import subprocess
import json
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# ✅ Force FFmpeg path inside Docker/Render
os.environ["FFMPEG_BINARY"] = "/usr/bin/ffmpeg"
os.environ["FFPROBE_BINARY"] = "/usr/bin/ffprobe"

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))     # backend/
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
USERS_FILE = os.path.join(BASE_DIR, "users.json")


# =====================================================
# ✅ LOGIN API
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
# ✅ SERVE FRONTEND FILES
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
# ✅ VIDEO GENERATION API
# =====================================================
@app.post("/api/generate_video")
def generate_video():
    try:
        poster = request.files.get("poster")
        bg_music = request.files.get("bg_music")
        voice_over = request.files.get("voice_over")

        if not poster:
            return jsonify({"error": "Poster image is required"}), 400

        # ✅ Create temp directory for FFmpeg
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

        # ------------------------------------------------------
        # ✅ SAFE ffprobe function (prevents worker crash)
        # ------------------------------------------------------
        def get_audio_duration(path):
            try:
                result = subprocess.run(
                    [
                        os.environ["FFPROBE_BINARY"],
                        "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        path
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                return float(result.stdout.strip())
            except Exception:
                return 25  # fallback

        # ✅ Use voice duration if exists
        duration = get_audio_duration(voice_path) if voice_path else 25

        final_path = os.path.join(tmp, "final_video.mp4")

        # =====================================================
        # ✅ CASE 1 — Voice + Background Music
        # =====================================================
        if voice_path and bg_path:
            ffmpeg_cmd = [
                os.environ["FFMPEG_BINARY"], "-y",
                "-loop", "1", "-i", poster_path,
                "-i", bg_path,
                "-i", voice_path,

                "-filter_complex",
                "[1:a]volume=0.25[a_bg];"
                "[a_bg][2:a]amix=inputs=2:duration=longest[a_mix]",

                "-map", "0:v",
                "-map", "[a_mix]",
                "-t", str(duration),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-shortest",
                final_path
            ]

        # =====================================================
        # ✅ CASE 2 — Only Voice
        # =====================================================
        elif voice_path:
            ffmpeg_cmd = [
                os.environ["FFMPEG_BINARY"], "-y",
                "-loop", "1", "-i", poster_path,
                "-i", voice_path,

                "-map", "0:v",
                "-map", "1:a",
                "-t", str(duration),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-shortest",
                final_path
            ]

        # =====================================================
        # ✅ CASE 3 — Only Background Music
        # =====================================================
        elif bg_path:
            ffmpeg_cmd = [
                os.environ["FFMPEG_BINARY"], "-y",
                "-loop", "1", "-i", poster_path,
                "-i", bg_path,

                "-filter_complex",
                "[1:a]volume=0.25[a_bg]",

                "-map", "0:v",
                "-map", "[a_bg]",
                "-t", "25",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-shortest",
                final_path
            ]

        # =====================================================
        # ✅ CASE 4 — No Audio
        # =====================================================
        else:
            ffmpeg_cmd = [
                os.environ["FFMPEG_BINARY"], "-y",
                "-loop", "1", "-i", poster_path,
                "-t", "25",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                final_path
            ]

        # ------------------------------------------------------
        # ✅ Log final FFmpeg command
        # ------------------------------------------------------
        print("\n✅ FINAL FFMPEG COMMAND:")
        print(" ".join(ffmpeg_cmd))

        # ------------------------------------------------------
        # ✅ Execute FFmpeg
        # ------------------------------------------------------
        process = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # ✅ Debug logs (Render console)
        print("\n✅ FFmpeg STDOUT:\n", process.stdout)
        print("\n✅ FFmpeg STDERR:\n", process.stderr)

        if process.returncode != 0:
            return jsonify({"error": "FFmpeg failed", "details": process.stderr}), 500

        return send_file(final_path, as_attachment=True)

    except Exception as e:
        print("🔥 ERROR:", e)
        return jsonify({"error": str(e)}), 500


# =====================================================
# ✅ LOCAL DEBUG MODE
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
