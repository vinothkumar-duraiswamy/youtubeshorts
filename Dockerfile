FROM python:3.10

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app

COPY backend /app/backend
COPY frontend /app/frontend

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

WORKDIR /app/backend

# Railway will inject PORT environment variable
CMD gunicorn --bind 0.0.0.0:$PORT app:app
