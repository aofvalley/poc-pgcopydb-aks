FROM python:3.11-slim

# Establecer etiquetas para documentación
LABEL version="1.0"
LABEL description="API REST para pgcopydb en Azure Kubernetes Service"

# Evitar diálogos interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Establecer directorios de trabajo
WORKDIR /app

# Instalar dependencias del sistema y configurar repositorios de PostgreSQL 17
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    curl \
    procps \
    && echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    # Instalar específicamente cliente PostgreSQL 17 y dependencias
    && apt-get install -y postgresql-client-17 libpq-dev \
    # Instalar la última versión de pgcopydb para compatibilidad con PG 17
    && apt-get install -y pgcopydb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Definir variables de entorno
ENV PG_VERSION=17
ENV PGCOPYDB_VERSION=0.17
ENV PORT=8000
ENV LOG_LEVEL=INFO
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copiar los archivos de requisitos primero para aprovechar el caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear un usuario no root para seguridad
RUN groupadd -r apiuser && \
    useradd -r -g apiuser -d /app -s /bin/bash apiuser && \
    chown -R apiuser:apiuser /app

# Copiar el resto de los archivos
COPY . .

# Asegurar que el usuario no-root tenga permisos adecuados
RUN chown -R apiuser:apiuser /app

# Crear archivo de healthcheck
RUN echo '#!/bin/bash\n\
curl -f http://localhost:$PORT/health || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# Definir healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD /app/healthcheck.sh

# Cambiar al usuario no-root
USER apiuser

# Exponer el puerto
EXPOSE $PORT

# Ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
