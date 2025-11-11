FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# --- LÍNEA DE DEBUG ---
# Esto mostrará en los logs de construcción qué archivos terminaron realmente en la carpeta /app
RUN ls -la /app
# ----------------------

CMD sh -c "voila app.ipynb --port=$PORT --no-browser --Voila.ip=0.0.0.0 --theme=light --show_tracebacks=True"
