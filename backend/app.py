import os
import uuid
import subprocess
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# -----------------------------------------------------------
# Flask App Setup
# -----------------------------------------------------------
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes (Netlify support)

# Use Railway’s writable temp folder
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Login credentials
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

    # Choose filter/mapping logic
    if bg_path and voice_path:
        audio_filter = [
            "-filter_complex", "[1:a][2:a]amix=inputs=2[aout]",
            "-map", "0:v", "-map", "[aout]"
        ]
    elif bg_path:
        audio_filter = ["-map", "0:v", "-map", "1:a"]
    elif voice_path:
        audio_filter = ["-map", "0:v", "-map", "1:a"]
    else:
        # Create silent audio when none provided
        audio_filter = ["-f", "lavfi", "-i", "anullsrc", "-shortest"]

    cmd += audio_filter

    # -------------------------------------------------------
    # Add lightweight FFmpeg video settings
    # -------------------------------------------------------
    cmd += [
        "-t", "15",  # video duration
        "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,"
               "pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
        "-c:a", "aac", "-shortest",
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
    # Return video file if created
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
        print("❌ FFmpeg failed or empty output.")
        return jsonify({"error": "Video generation failed. Check logs."}), 500


# -----------------------------------------------------------
# HEALTH CHECK
# -----------------------------------------------------------
@app.route("/")
def home():
    return jsonify({"status": "Backend is running!"})


# -----------------------------------------------------------
# RUN APP LOCALLY (for testing)
# -----------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
