FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código
COPY . .

# --- CAMBIO CLAVE ---
# Dar permisos de ejecución al script y definirlo como comando de inicio
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]
