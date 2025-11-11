FROM python:3.10-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

WORKDIR /app

# Copy backend
COPY backend /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create uploads folder
RUN mkdir -p /app/uploads

# Expose Railway port
ENV PORT=10000

CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
