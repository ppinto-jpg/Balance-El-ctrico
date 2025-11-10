# Usa una imagen base de Python ligera
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# 1. Instala las dependencias del sistema (APT)
# Actualiza los repositorios e instala 'graphviz' (la herramienta de sistema)
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# 2. Instala las dependencias de Python (PIP)
# Copia solo el archivo de requisitos primero para aprovechar el caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copia el resto de tu proyecto
# Esto incluye tu archivo .ipynb (ej. app.ipynb) y cualquier otro archivo
COPY . .

# 4. Configura el entorno
# Render (y otros) proveen una variable $PORT. Usamos 10000 como default.
ENV PORT 10000
EXPOSE $PORT

# 5. Define el comando para correr la aplicación (CORREGIDO)
# Este es el "start command". 
# Asegúrate de que tu notebook se llame 'app.ipynb'
CMD voila app.ipynb --port=$PORT --ip=0.0.0.0 --no-browser
