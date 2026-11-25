FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HEADLESS_CLOUD=1 \
    TZ=Asia/Jakarta

# Install FFmpeg and clean Linux TrueType fonts for Pillow + libass burned subtitles
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fontconfig \
    fonts-dejavu-core \
    fonts-liberation \
    ca-certificates \
    tzdata \
    && fc-cache -f \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ ./config/
COPY src/ ./src/
COPY tests/ ./tests/

RUN mkdir -p /app/output \
    && useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["python", "-m", "src.pipeline"]
CMD ["--publish-mode", "draft"]
