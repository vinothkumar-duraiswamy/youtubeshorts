import os
import uuid
import subprocess
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# -----------------------------------------------------------
# Flask App Setup
# -----------------------------------------------------------
app = Flask(__name__)
CORS(app)  # Enable CORS for Netlify frontend

# Writable folder (Railway safe)
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Working Login Credentials
USERNAME = "vinothkumar"
PASSWORD = "admin123"


# -----------------------------------------------------------
# LOGIN ENDPOINT
# -----------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == USERNAME and password == PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False}), 401


# -----------------------------------------------------------
# VIDEO GENERATION ENDPOINT
# -----------------------------------------------------------
@app.route("/api/generate_video", methods=["POST"])
def generate_video():
    print("✅ Received /api/generate_video request")

    poster = request.files.get("poster")
    bg_music = request.files.get("bg_music")
    voice_over = request.files.get("voice_over")

    if not poster:
        return jsonify({"error": "Poster image required"}), 400

    # -------------------------------------------------------
    # Save uploaded files
    # -------------------------------------------------------
    poster_path = os.path.join(UPLOAD_FOLDER, f"poster_{uuid.uuid4()}.png")
    poster.save(poster_path)

    bg_path = None
    if bg_music:
        bg_path = os.path.join(UPLOAD_FOLDER, f"bg_{uuid.uuid4()}.mp3")
        bg_music.save(bg_path)

    voice_path = None
    if voice_over:
        voice_path = os.path.join(UPLOAD_FOLDER, f"voice_{uuid.uuid4()}.mp3")
        voice_over.save(voice_path)

    output_path = os.path.join(UPLOAD_FOLDER, f"final_{uuid.uuid4()}.mp4")

    # -------------------------------------------------------
    # Build FFmpeg Command
    # -------------------------------------------------------
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", poster_path]

    if bg_path:
        cmd += ["-i", bg_path]
    if voice_path:
        cmd += ["-i", voice_path]

    # -------------------------------------------------------
    # AUDIO MIXING LOGIC (with dynamic volume)
    # -------------------------------------------------------
    music_volume = request.form.get("music_volume", "30")
    try:
        user_volume = float(music_volume)
    except ValueError:
        user_volume = 30.0

    bg_volume_level = round(user_volume / 100, 2)  # convert to 0.0–1.0 range

    if bg_path and voice_path:
        # ✅ Dynamic background music volume + normalize
        filters = [
            "-filter_complex",
            f"[1:a]volume={bg_volume_level}[a1];"
            "[2:a]volume=1.0[a2];"
            "[a1][a2]amix=inputs=2:duration=longest:dropout_transition=2[aout];"
            "[aout]loudnorm[audio_final]",
            "-map", "0:v", "-map", "[audio_final]"
        ]
    elif bg_path:
        filters = ["-map", "0:v", "-map", "1:a"]
    elif voice_path:
        filters = ["-map", "0:v", "-map", "1:a"]
    else:
        filters = ["-f", "lavfi", "-i", "anullsrc", "-shortest"]

    cmd += filters

    # -------------------------------------------------------
    # Video Encoding Settings
    # -------------------------------------------------------
    cmd += [
        "-t", "15",  # duration in seconds
        "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,"
               "pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "30",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]

    print("✅ Running FFmpeg command:")
    print(" ".join(cmd))

    # -------------------------------------------------------
    # Execute FFmpeg
    # -------------------------------------------------------
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()

    print("🔵 FFmpeg STDOUT:\n", stdout)
    print("🔴 FFmpeg STDERR:\n", stderr)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        print("✅ FFmpeg Completed Successfully!")
        return send_file(
            output_path,
            as_attachment=True,
            download_name="final_video.mp4",
            mimetype="video/mp4"
        )
    else:
        print("❌ FFmpeg failed or output file too small.")
        return jsonify({"error": "Video generation failed."}), 500


# -----------------------------------------------------------
# HEALTH CHECK
# -----------------------------------------------------------
@app.route("/")
def home():
    return jsonify({"status": "Backend is running!"})


# -----------------------------------------------------------
# LOCAL RUN
# -----------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
