# Usar la imagen oficial de Debian como base
FROM debian:bullseye-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema, pgcopydb y limpiar después
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    curl \
    && echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    # Instalar específicamente cliente PostgreSQL 17 y dependencias
    && apt-get install -y postgresql-client-17 libpq-dev \
    # Instalar la última versión de pgcopydb
    && apt-get install -y pgcopydb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Definir variable de entorno para PostgreSQL 17
ENV PG_VERSION=17

# Crear un directorio para backups y asignar permisos adecuados
RUN mkdir -p /app/backups && chmod 777 /app/backups

# Comando por defecto
CMD ["pgcopydb", "--version"]
