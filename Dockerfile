FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev ffmpeg \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy backend and frontend separately
COPY backend /app/backend
COPY frontend /app/frontend

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /app/backend/requirements.txt

# Expose port
EXPOSE 5000

# Start Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "backend.app:app"]
