FROM python:3.12-slim

RUN apt-get update && apt-get install -y wget gnupg curl unzip ca-certificates \
  fonts-liberation libnss3 libatk-bridge2.0-0 libgtk-3-0 libxss1 libasound2 libxshmfence1 \
  libgbm1 libxrandr2 libxdamage1 libxcomposite1 libx11-xcb1 libxinerama1 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt && playwright install --with-deps

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
