FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema, pgcopydb y limpiar después
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    lsb-release \
    curl \
    && curl -L https://dl.k8s.io/apt/doc/apt-key.gpg | apt-key add - \
    && echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && apt-get update \
    && apt-get install -y pgcopydb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar los archivos de requisitos primero para aprovechar el caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos
COPY . .

# Exponer el puerto (actualizado a 8000 para coincidir con main.py)
EXPOSE 8000

# Ejecutar la aplicación
CMD ["python", "main.py"]
