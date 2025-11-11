FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CAMBIOS PARA AHORRAR MEMORIA:
# 1. Eliminado --preheat_kernel=True (consume RAM antes de tiempo)
# 2. Agregado --Voila.pool_size=0 (no mantiene kernels extra en espera)
# 3. Agregado --VoilaExecutor.timeout=600 (da más tiempo antes de matar un proceso lento, por si la CPU está saturada)

CMD sh -c "voila app.ipynb --port=$PORT --no-browser --Voila.ip=0.0.0.0 --theme=light --Voila.pool_size=0 --VoilaConfiguration.file_allowlist=\"['.*']\""
