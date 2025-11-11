import os
import uuid
from flask import Flask, request, jsonify, send_file
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = "/app/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Temporary login
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

    # ✅ Build FFmpeg filters
    base_cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", poster_path,
        "-t", "15",
    ]

    audio_inputs = []
    filter_complex = ""
    maps = []

    # ✅ Add background music
    if bg_path:
        base_cmd += ["-i", bg_path]
        audio_inputs.append("1")

    # ✅ Add voice-over
    if voice_path:
        base_cmd += ["-i", voice_path]
        audio_inputs.append("2" if bg_path else "1")

    # ✅ Audio mixing logic
    if len(audio_inputs) == 0:
        # ❌ No audio → create silent track
        filter_complex = "anullsrc=channel_layout=stereo:sample_rate=44100[a0]"
        maps = ["-map", "0:v", "-map", "[a0]"]

    elif len(audio_inputs) == 1:
        # ✅ Only one audio source → no mix needed
        maps = ["-map", "0:v", "-map", f"{audio_inputs[0]}:a"]

    elif len(audio_inputs) == 2:
        # ✅ Mix background + voice-over
        filter_complex = (
            f"[1:a][2:a]amix=inputs=2:duration=longest:dropout_transition=2[aout]"
        )
        maps = ["-map", "0:v", "-map", "[aout]"]

    # ✅ FULL FFmpeg Command
    cmd = base_cmd

    if filter_complex:
        cmd += ["-filter_complex", filter_complex]

    cmd += maps

    # ✅ Video encoding
    cmd += [
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "28",
        output_path
    ]

    print("✅ Running FFmpeg command:")
    print(" ".join(cmd))

    # ✅ Run FFmpeg
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    _, stderr = process.communicate()

    print("🔴 FFmpeg Output:")
    print(stderr)

    if not os.path.exists(output_path):
        return jsonify({"error": "FFmpeg failed"}), 500

    return send_file(output_path, mimetype="video/mp4")


@app.route("/")
def home():
    return "Backend is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
