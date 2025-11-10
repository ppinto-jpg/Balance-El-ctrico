#!/bin/bash
# entrypoint.sh

# Imprimir el comando para verificar en logs
echo "Iniciando Voila en el puerto $PORT..."

# Ejecutar Voila con todas las banderas de seguridad relajadas
# Usamos exec para que Voila sea el proceso principal (PID 1)
exec voila app.py \
    --port=$PORT \
    --no-browser \
    --Voila.ip=0.0.0.0 \
    --VoilaConfiguration.file_allowlist="['.*']" \
    --Voila.base_url="/" \
    --theme=light \
    --debug
