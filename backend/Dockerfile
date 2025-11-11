# Use Python base image
FROM python:3.12-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Create working dir
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Expose port 5000
EXPOSE 5000

# Gunicorn command
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
