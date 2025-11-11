FROM jrottenberg/ffmpeg:6.0-ubuntu

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip python3-dev

WORKDIR /app

COPY . /app

RUN pip3 install --no-cache-dir -r backend/requirements.txt

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "--timeout", "600", "--workers", "1", "backend.app:app"]
