#!/bin/bash

echo "Iniciando pgcopydb container en modo servidor..."
echo "El contenedor está listo para recibir comandos via docker exec"

# Configurar directorios y permisos
BASE_DIR="/app/pgcopydb_files"
LOG_DIR="${BASE_DIR}/logs"
TEMP_DIR="${BASE_DIR}/temp_storage"
BACKUP_DIR="${BASE_DIR}/backups"

# Intentar crear directorios con manejo de errores
for DIR in "${LOG_DIR}" "${TEMP_DIR}" "${BACKUP_DIR}"; do
    if [ ! -d "$DIR" ]; then
        mkdir -p "$DIR" || {
            echo "ERROR: No se pudo crear el directorio $DIR. Creando en /tmp como alternativa."
            if [[ "$DIR" == "${LOG_DIR}" ]]; then
                LOG_DIR="/tmp/pgcopydb/logs"
            elif [[ "$DIR" == "${TEMP_DIR}" ]]; then
                TEMP_DIR="/tmp/pgcopydb/temp"
            else
                BACKUP_DIR="/tmp/pgcopydb/backups"
            fi
            mkdir -p "$LOG_DIR" "$TEMP_DIR" "$BACKUP_DIR"
        }
    fi
done

# Definir archivo de log
LOG_FILE="${LOG_DIR}/pgcopydb-server.log"
touch "$LOG_FILE" || {
    echo "ERROR: No se pudo crear el archivo de log en $LOG_FILE. Usando /tmp/pgcopydb-server.log"
    LOG_FILE="/tmp/pgcopydb-server.log"
    touch "$LOG_FILE"
}

# Iniciar log
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