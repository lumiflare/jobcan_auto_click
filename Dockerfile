FROM python:3.9-slim

# Install Chromium and Chromedriver
# We use chromium because google-chrome-stable is not available for Linux ARM64 (Apple Silicon)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variable to tell script we are in Docker
ENV IS_DOCKER=true

CMD ["python", "-u", "jobcan_bot.py"]
