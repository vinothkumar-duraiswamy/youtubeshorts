from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import uuid
import subprocess
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/app/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/api/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "1234":
        return jsonify({"success": True})
    
    return jsonify({"success": False})


@app.route("/api/generate_video", methods=["POST"])
def generate_video():
    try:
        print("🔵 Received /api/generate_video request")

        # ✅ Read uploaded files
        poster = request.files.get("poster")
        bg_music = request.files.get("bg_music")
        voice_over = request.files.get("voice_over")

        if not poster:
            return jsonify({"error": "Poster image missing"}), 400

        # ✅ Save temporary files
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

        output_video = os.path.join(UPLOAD_FOLDER, f"final_{uuid.uuid4()}.mp4")

        # ✅ FFmpeg Base Command
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", poster_path,
            "-t", "15",
        ]

        # ✅ Add audio tracks
        audio_inputs = []
        filter_complex = []

        if voice_path:
            ffmpeg_cmd += ["-i", voice_path]
            audio_inputs.append("1:a")

            if bg_path:
                ffmpeg_cmd += ["-i", bg_path]
                audio_inputs.append("2:a")
        elif bg_path:
            ffmpeg_cmd += ["-i", bg_path]
            audio_inputs.append("1:a")

        # ✅ If multiple audio inputs → mixdown
        if len(audio_inputs) > 1:
            filter_complex.append(
                f"[{audio_inputs[0]}][{audio_inputs[1]}]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            ffmpeg_cmd += ["-filter_complex", ";".join(filter_complex), "-map", "0:v", "-map", "[aout]"]
        elif len(audio_inputs) == 1:
            ffmpeg_cmd += ["-map", "0:v", "-map", audio_inputs[0]]
        else:
            # no audio
            pass

        # ✅ Encoding settings
        ffmpeg_cmd += [
            "-vf", "scale=1080:1920",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            "-crf", "28",
            output_video
        ]

        print("✅ Running FFmpeg command:")
        print(" ".join(ffmpeg_cmd))

        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        print("🔴 FFmpeg Output:")
        print(process.stderr)

        if not os.path.exists(output_video):
            return jsonify({"error": "FFmpeg failed"}), 500

        return send_file(output_video, mimetype="video/mp4", as_attachment=True, download_name="final_video.mp4")

    except Exception as e:
        print("🔥 ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "✅ Backend Running on Railway!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
