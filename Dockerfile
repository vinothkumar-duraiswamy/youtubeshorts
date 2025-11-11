# ✅ Base image with FFmpeg
FROM jrottenberg/ffmpeg:6.0-ubuntu

# ✅ Install Python
RUN apt-get update && apt-get install -y python3 python3-pip python3-dev

# ✅ Set working directory
WORKDIR /app

# ✅ Copy project
COPY . /app

# ✅ Install dependencies
RUN pip3 install --no-cache-dir -r backend/requirements.txt

# ✅ Expose port (Railway will assign dynamically)
EXPOSE 5000

# ✅ Start server
CMD ["gunicorn", "backend.app:app", "-b", "0.0.0.0:5000"]
