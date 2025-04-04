FROM python:3.11-slim

WORKDIR /app

# Copiar los archivos de requisitos primero para aprovechar el caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos
COPY . .

# Exponer el puerto
EXPOSE 3000

# Ejecutar la aplicación
CMD ["python", "main.py"]
