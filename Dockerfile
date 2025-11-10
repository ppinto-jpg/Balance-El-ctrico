FROM python:3.10-slim

# Instalar dependencias básicas
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos (incluido app.py)
COPY . .

# Configurar el comando de inicio para usar app.py
# NOTA: Voila puede ejecutar scripts .py directamente y es mucho más robusto.
CMD voila app.py --Voila.port=$PORT --Voila.ip=0.0.0.0 --no-browser --theme=light
