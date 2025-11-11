FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev ffmpeg \
    && apt-get clean

WORKDIR /app

COPY backend /app/backend
COPY frontend /app/frontend

RUN pip3 install --no-cache-dir -r /app/backend/requirements.txt

EXPOSE 5000

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} backend.app:app"]
