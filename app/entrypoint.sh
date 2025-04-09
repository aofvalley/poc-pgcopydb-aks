#!/bin/bash

echo "Iniciando pgcopydb container en modo servidor..."
echo "El contenedor está listo para recibir comandos via docker exec"

# Configurar log para monitoreo
LOG_DIR="/app/pgcopydb_files/logs"
mkdir -p ${LOG_DIR}
LOG_FILE="${LOG_DIR}/pgcopydb-server.log"

echo "$(date): Contenedor pgcopydb iniciado y listo para comandos" > ${LOG_FILE}

# Verificar versión e información de pgcopydb
echo "=== Información de pgcopydb ===" >> ${LOG_FILE}
pgcopydb --version >> ${LOG_FILE} 2>&1
echo "============================" >> ${LOG_FILE}

echo "Los logs se guardarán en: ${LOG_FILE}"

# Mantener el contenedor en ejecución
tail -f ${LOG_FILE} &

# Bucle infinito para mantener el contenedor ejecutándose
while true; do
    sleep 60
    # Comprobar si hay errores o problemas
    if [ -f "${LOG_DIR}/health_check.fail" ]; then
        echo "$(date): Error detectado en el health check" >> ${LOG_FILE}
    fi
    echo "$(date): pgcopydb container está activo" >> ${LOG_FILE}
done