# ✅ Base image with FFmpeg
FROM jrottenberg/ffmpeg:6.0-ubuntu

# ✅ Install Python
RUN apt-get update && apt-get install -y python3 python3-pip python3-dev

# ✅ Set working directory
WORKDIR /app

# ✅ Copy project
COPY . /app

# ✅ Install Python dependencies
RUN pip3 install --no-cache-dir -r backend/requirements.txt

# ✅ Expose Railway’s dynamic port
EXPOSE 5000

# ✅ USE RAILWAY PORT IN GUNICORN (VERY IMPORTANT)
CMD ["bash", "-c", "gunicorn -b 0.0.0.0:$PORT backend.app:app"]
