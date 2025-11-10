# Usa una imagen base de Python ligera
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# 1. Instala las dependencias del sistema (APT)
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# 2. Instala las dependencias de Python (PIP)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copia el resto de tu proyecto
COPY . .

# 4. Configura el entorno
ENV PORT 10000
EXPOSE $PORT

# 5. Define el comando para correr la aplicación (¡VERSIÓN ROBUSTA!)
# Se usan los "Traitlets" completos (--Voila.ip) que son universales
CMD voila Balance-E-Full_App.ipynb --Voila.port=$PORT --Voila.ip=0.0.0.0 --no-browser
