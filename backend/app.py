import os
import uuid
import subprocess
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# -----------------------------------------------------------
# Flask App Setup
# -----------------------------------------------------------
app = Flask(__name__)
CORS(app)  # Allow frontend (Netlify) requests

# Writable folder for Railway
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Basic Login (temporary static)
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

    # Collect uploaded files
    poster = request.files.get("poster")
    bg_music = request.files.get("bg_music")
    voice_over = request.files.get("voice_over")

    if not poster:
        return jsonify({"error": "Poster image required"}), 400

    # -------------------------------------------------------
    # Save input files
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
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", poster_path
    ]

    # Add optional inputs
    if bg_path:
        cmd += ["-i", bg_path]
    if voice_path:
        cmd += ["-i", voice_path]

    # -------------------------------------------------------
    # AUDIO MIX LOGIC
    # -------------------------------------------------------
    if bg_path and voice_path:
        # ✅ Voiceover + background music mix (music lowered to 30%)
        filters = [
            "-filter_complex",
            "[1:a]volume=0.3[a1];[2:a]volume=1.0[a2];"
            "[a1][a2]amix=inputs=2:duration=longest[aout]",
            "-map", "0:v", "-map", "[aout]"
        ]
    elif bg_path:
        # ✅ Only background music
        filters = ["-map", "0:v", "-map", "1:a"]
    elif voice_path:
        # ✅ Only voiceover
        filters = ["-map", "0:v", "-map", "1:a"]
    else:
        # ✅ No audio → add silent track
        filters = ["-f", "lavfi", "-i", "anullsrc", "-shortest"]

    cmd += filters

    # -------------------------------------------------------
    # FFmpeg Video Settings
    # -------------------------------------------------------
    cmd += [
        "-t", "15",  # Duration
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

    # -------------------------------------------------------
    # Return output
    # -------------------------------------------------------
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        print("✅ FFmpeg Completed Successfully!")
        return send_file(
            output_path,
            as_attachment=True,
            download_name="final_video.mp4",
            mimetype="video/mp4"
        )
    else:
        print("❌ FFmpeg failed or empty output file.")
        return jsonify({"error": "Video generation failed."}), 500


# -----------------------------------------------------------
# HEALTH CHECK
# -----------------------------------------------------------
@app.route("/")
def home():
    return jsonify({"status": "Backend is running!"})


# -----------------------------------------------------------
# RUN LOCALLY
# -----------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
