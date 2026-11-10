FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir instaloader python-telegram-bot flask qrcode[pil] pillow yt-dlp google-generativeai
COPY . .
CMD ["python", "app.py"]
