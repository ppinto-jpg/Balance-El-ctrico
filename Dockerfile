FROM python:3.10-slim

# 1. Configuración de entorno crítica para Render
ENV PYTHONUNBUFFERED=1

# 2. Instalar dependencias del sistema (Graphviz)
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Instalar librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el código Y el archivo de configuración nuevo
COPY . .

# 5. Comando de inicio ROBUSTO.
# Ya no necesitamos pasar tantos flags porque están en voila.json.
# Solo necesitamos asegurarnos de que el puerto se pase correctamente.
CMD ["sh", "-c", "voila app.py --port=$PORT"]
