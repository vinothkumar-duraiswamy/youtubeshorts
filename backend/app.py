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

    # Get background music volume
    music_volume = request.form.get("music_volume", "30")
    try:
        user_volume = float(music_volume)
    except ValueError:
        user_volume = 30.0
    bg_volume_level = round(user_volume / 100, 2)

    # ✅ Set base FFmpeg command (minimal threads + smaller buffer)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-threads", "1",
        "-loop", "1", "-i", poster_path
    ]

    # Add audio inputs
    input_count = 0
    if bg_path:
        cmd += ["-i", bg_path]
        input_count += 1
    if voice_path:
        cmd += ["-i", voice_path]
        input_count += 1

    filter_complex = ""
    maps = []

    # ✅ Build optimized filter for mixing
    if bg_path and voice_path:
        filter_complex = (
            f"[1:a]volume={bg_volume_level}[bg];"
            f"[2:a]volume=1.0[voice];"
            f"[bg][voice]amix=inputs=2:duration=longest:dropout_transition=2[aout]"
        )
        maps = ["-map", "0:v", "-map", "[aout]"]

    elif bg_path:
        maps = ["-map", "0:v", "-map", "1:a"]

    elif voice_path:
        maps = ["-map", "0:v", "-map", "1:a"]

    else:
        # ✅ If no audio, create silent track (low CPU)
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        maps = ["-map", "0:v", "-map", "1:a"]

    if filter_complex:
        cmd += ["-filter_complex", filter_complex]

    cmd += maps

    # ✅ Lightweight encoding setup
    cmd += [
        "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,"
               "pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "superfast",      # 💡 Less CPU usage
        "-crf", "32",                # 💡 Slightly more compression
        "-c:a", "aac",
        "-b:a", "96k",               # 💡 Lower audio bitrate to save RAM
        "-pix_fmt", "yuv420p",
        "-to", "60",                 # ⏱ Limit max duration to 60s
        "-shortest",
        output_path
    ]

    print("🎬 Running FFmpeg command:\n", " ".join(cmd))

    try:
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print("🔴 FFmpeg STDERR:\n", process.stderr)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Video generation timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if os.path.exists(output_path) and os.path.getsize(output_path) > 50000:
        print("✅ FFmpeg Completed Successfully!")
        return send_file(output_path, as_attachment=True,
                         download_name="final_video.mp4", mimetype="video/mp4")

    print("❌ FFmpeg failed or file empty.")
    return jsonify({"error": "Video generation failed"}), 500


@app.route("/")
def home():
    return jsonify({"status": "Backend running!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
