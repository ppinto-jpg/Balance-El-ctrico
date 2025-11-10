# Usa una imagen de Python ligera y moderna
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Actualiza el sistema e instala dependencias básicas si hicieran falta
# (Graphviz ya no es estrictamente necesario con tu última versión de código, 
# pero lo dejamos por seguridad si alguna librería lo pide internamente)
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Copia y estala los requerimientos de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos de tu proyecto
COPY . .

# Configura el puerto para Render
ENV PORT=10000
EXPOSE $PORT

# Comando de inicio ROBUSTO para Voila en Render
# NOTA: Si tu archivo se llama distinto a 'app.ipynb', cámbialo aquí.
CMD voila app.ipynb --Voila.ip=0.0.0.0 --Voila.port=$PORT --no-browser --Voila.base_url=/ --theme=light
