# Usar la imagen oficial de pgcopydb
FROM dimitri/pgcopydb:v0.17

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar scripts personalizados
COPY scripts/ /app/scripts/

# Exponer el puerto 8080 (si es necesario)
EXPOSE 8080

# Comando por defecto
CMD ["pgcopydb", "--help"]
