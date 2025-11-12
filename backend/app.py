import os
import uuid
import subprocess
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

USERNAME = "vinothkumar"
PASSWORD = "admin123"


@app.route("/api/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == USERNAME and password == PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False}), 401


@app.route("/api/generate_video", methods=["POST"])
def generate_video():
    print("✅ Received /api/generate_video request")

    poster = request.files.get("poster")
    bg_music = request.files.get("bg_music")
    voice_over = request.files.get("voice_over")

    if not poster:
        return jsonify({"error": "Poster image required"}), 400

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

    # Get background volume from frontend
    music_volume = request.form.get("music_volume", "30")
    try:
        user_volume = float(music_volume)
    except ValueError:
        user_volume = 30.0
    bg_volume_level = round(user_volume / 100, 2)

    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", poster_path]

    # Add optional audio
    if bg_path:
        cmd += ["-i", bg_path]
    if voice_path:
        cmd += ["-i", voice_path]

    # Build filters
    filter_complex = ""
    maps = []

    if bg_path and voice_path:
        filter_complex = (
            f"[1:a]volume={bg_volume_level}[bg];"
            f"[2:a]volume=1.0[voice];"
            f"[bg][voice]amix=inputs=2:duration=longest[aout]"
        )
        maps = ["-map", "0:v", "-map", "[aout]"]
    elif bg_path:
        maps = ["-map", "0:v", "-map", "1:a"]
    elif voice_path:
        maps = ["-map", "0:v", "-map", "1:a"]
    else:
        # No audio → generate silent audio
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        maps = ["-map", "0:v", "-map", "1:a"]

    if filter_complex:
        cmd += ["-filter_complex", filter_complex]

    cmd += maps
    cmd += [
        "-t", "60",
        "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,"
               "pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "30",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]

    print("🎬 Running FFmpeg command:\n", " ".join(cmd))

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()

    print("🔵 FFmpeg STDOUT:\n", stdout)
    print("🔴 FFmpeg STDERR:\n", stderr)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        print("✅ FFmpeg Completed Successfully!")
        return send_file(output_path, as_attachment=True, download_name="final_video.mp4", mimetype="video/mp4")
    else:
        print("❌ FFmpeg failed or file empty.")
        return jsonify({"error": "Video generation failed"}), 500


@app.route("/")
def home():
    return jsonify({"status": "Backend running!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

