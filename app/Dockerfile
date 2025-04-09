# Usar la imagen oficial de Debian como base
FROM debian:bullseye-slim

# Establecer etiquetas para documentación
LABEL version="1.1"
LABEL description="Pgcopydb tool for PostgreSQL 17 compatibility"

# Evitar diálogos interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema y pgcopydb usando una única capa para reducir el tamaño de la imagen
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    curl \
    netcat \
    procps \
    && echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    # Instalar específicamente cliente PostgreSQL 17 y pgcopydb
    && apt-get install -y postgresql-client-17 libpq-dev pgcopydb \
    # Limpiar el caché de apt para reducir el tamaño de la imagen
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Definir variable de entorno para PostgreSQL 17
ENV PG_VERSION=17

# Crear estructura de directorios para pgcopydb_files
RUN mkdir -p /app/pgcopydb_files/backups && \
    mkdir -p /app/pgcopydb_files/temp_storage && \
    mkdir -p /app/pgcopydb_files/logs

# Establecer permisos adecuados
RUN chmod -R 777 /app/pgcopydb_files

# Crear un usuario no-root
RUN groupadd -r pgcopydb && \
    useradd -r -g pgcopydb -d /app -s /bin/bash pgcopydb && \
    chown -R pgcopydb:pgcopydb /app

# Definir variables de entorno para los directorios
ENV PGCOPYDB_TEMP_DIR=/app/pgcopydb_files/temp_storage
ENV PGCOPYDB_BACKUP_DIR=/app/pgcopydb_files/backups
ENV PGCOPYDB_LOG_DIR=/app/pgcopydb_files/logs

# Volumen para persistencia de datos
VOLUME ["/app/pgcopydb_files"]

# Script de healthcheck
COPY ./healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh

# Copiar el script de entrypoint
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Definir healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD /app/healthcheck.sh

# Cambiar al usuario no-root
USER pgcopydb

# Exponer puerto en caso de que se añada una API o interfaz web en el futuro
EXPOSE 8080

# Usar el nuevo script de entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
