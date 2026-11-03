FROM python:3.11-slim
# gcc builds spidev (used by the Enviro+ LCD library), which has no ready-made ARM wheel
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
EXPOSE 8000
CMD ["python", "-u", "main.py"]
