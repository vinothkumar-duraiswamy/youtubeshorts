# ✅ Base Image (Python + FFmpeg included)
FROM jrottenberg/ffmpeg:6.0-ubuntu

# ✅ Install Python
RUN apt-get update && apt-get install -y python3 python3-pip python3-dev

# ✅ Set work directory
WORKDIR /app

# ✅ Copy project files
COPY . /app

# ✅ Install Python dependencies
RUN pip3 install --no-cache-dir -r backend/requirements.txt

# ✅ Expose Render port
ENV PORT=10000

# ✅ Run Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "backend.app:app"]