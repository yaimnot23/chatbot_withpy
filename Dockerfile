FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY .env .
COPY db/ ./db/

# Hugging Face Spaces 기본 포트
EXPOSE 7860

CMD ["python", "server.py"]
