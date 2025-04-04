FROM dimitri/pgcopydb:latest

# Instalar dependencias adicionales si es necesario
RUN apt-get update && apt-get install -y curl

# Directorio de trabajo
WORKDIR /app

# Copiar scripts personalizados (si los necesitas)
COPY scripts/ /app/scripts/

# Exponer puerto (si es necesario, por ejemplo para una API)
EXPOSE 8080

# Comando por defecto (puedes cambiarlo más adelante al integrar la API)
CMD ["pgcopydb", "--help"]
