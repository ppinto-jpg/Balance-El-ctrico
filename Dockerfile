FROM python:3.10-slim

# Evita que Python haga buffer de stdout/stderr para ver logs en tiempo real en Render.
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema (Graphviz es necesario según tu código original)
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# COMANDO DE INICIO ACTUALIZADO:
# Se agregó --VoilaConfiguration.file_allowlist="['.*']" para evitar errores 403
CMD sh -c "voila app.py --port=$PORT --no-browser --theme=light --enable_nbextensions=True --Voila.ip=0.0.0.0 --VoilaConfiguration.file_allowlist=\"['.*']\""
