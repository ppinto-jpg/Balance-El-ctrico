FROM python:3.10-slim

# Muestra logs en tiempo real
ENV PYTHONUNBUFFERED=1

# Instalamos dependencias del sistema
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalamos librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto (incluyendo app.ipynb)
COPY . .

# Comando nativo de Voila para notebooks.
# Es mucho más estable que ejecutar .py directamente.
CMD sh -c "voila app.ipynb --port=$PORT --no-browser --Voila.ip=0.0.0.0 --theme=light --show_tracebacks=True"
