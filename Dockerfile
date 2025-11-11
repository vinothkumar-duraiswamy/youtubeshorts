FROM jrottenberg/ffmpeg:6.0-ubuntu

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    && apt-get clean

WORKDIR /app

COPY backend /app/backend
COPY frontend /app/frontend

RUN pip3 install --no-cache-dir -r /app/backend/requirements.txt

EXPOSE 10000

CMD ["gunicorn", "-b", "0.0.0.0:10000", "backend.app:app"]
