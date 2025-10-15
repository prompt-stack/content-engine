FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    postgresql-client \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp for YouTube extraction (always get latest version)
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp \
    && yt-dlp --version

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright for Article extractor (Reddit may also benefit from it)
RUN pip install playwright \
    && playwright install chromium \
    && playwright install-deps chromium

# Copy application code
COPY backend/ .

# Install Node.js dependencies for extractors
RUN cd extractors/youtube && npm install && \
    cd ../reddit && npm install && \
    cd ../tiktok && npm install && \
    cd ../article && npm install && \
    cd ../..

# Make start script executable
RUN chmod +x start.sh

# Expose port (Railway will set this dynamically)
EXPOSE 8000

# Run the startup script (runs migrations then starts server)
CMD ["./start.sh"]