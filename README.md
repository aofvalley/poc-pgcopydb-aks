# pgcopydb-aks

Herramienta para realizar clonación y migración de bases de datos PostgreSQL en entornos Docker y Kubernetes (AKS).

## Descripción

Este proyecto proporciona una solución para clonar, migrar y manipular bases de datos PostgreSQL utilizando [pgcopydb](https://github.com/dimitri/pgcopydb) en contenedores Docker. Incluye una API REST para interactuar con la herramienta remotamente.

## Estructura del Proyecto

```
pgcopydb-aks/
├── api/                   # Código fuente de la API REST
│   ├── Dockerfile         # Configuración para construir la imagen de la API
│   ├── main.py            # Aplicación FastAPI
│   └── requirements.txt   # Dependencias de Python
├── app/                   # Código fuente de la aplicación pgcopydb
│   ├── Dockerfile         # Configuración para construir la imagen de pgcopydb
│   ├── entrypoint.sh      # Script de punto de entrada para mantener el contenedor ejecutándose
│   └── healthcheck.sh     # Script para verificar el estado del contenedor
├── k8s/                   # Manifiestos de Kubernetes para despliegue
│   ├── pgcopydb-api-deployment.yaml
│   ├── pgcopydb-api-service.yaml
│   ├── pgcopydb-deployment.yaml
│   └── pgcopydb-pvc.yaml
└── pgcopydb-aks/          # Chart de Helm para despliegue en Kubernetes
    ├── Chart.yaml
    ├── values.yaml
    └── templates/         # Plantillas para el chart de Helm
```

## Requisitos Previos

- Docker instalado localmente
- Acceso a bases de datos PostgreSQL de origen y destino
- Docker Compose (opcional, para despliegue simplificado)

## Pasos para Ejecutar el Sistema con Monitoreo de Logs

Siga estos pasos para ejecutar el sistema localmente con Docker y habilitar el monitoreo de logs.

### 1. Construir las imágenes Docker

```bash
# Construir la imagen de pgcopydb
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/app
docker build -t pgcopydb-local:latest .

# Construir la imagen de la API REST
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/api
docker build -t pgcopydb-api-local:latest .
```

### 2. Crear una red Docker para la comunicación entre contenedores

```bash
docker network create pgcopydb-network
```

### 3. Crear un volumen para almacenamiento persistente

```bash
docker volume create pgcopydb-data
```

### 4. Ejecutar el contenedor pgcopydb

```bash
docker run -d --name pgcopydb-container \
  --network pgcopydb-network \
  -v pgcopydb-data:/app/pgcopydb_files \
  pgcopydb-local:latest
```

### 5. Ejecutar el contenedor de la API REST

```bash
docker run -d --name pgcopydb-api-container \
  --network pgcopydb-network \
  -p 8000:8000 \
  -v pgcopydb-data:/app/pgcopydb_files \
  pgcopydb-api-local:latest
```

### 6. Verificar que ambos contenedores están en ejecución

```bash
docker ps
```

Debería ver ambos contenedores `pgcopydb-container` y `pgcopydb-api-container` en estado "Up".

## Cómo Utilizar el Sistema

Una vez que el sistema esté ejecutándose, puede utilizar la API REST para realizar operaciones con pgcopydb.

### 1. Ejecutar una operación de clonación de base de datos

```bash
curl -X POST http://localhost:8000/clone \
  -H "Content-Type: application/json" \
  -d '{
    "source": "postgresql://usuario:contraseña@servidor-origen:5432/basedatos?sslmode=require",
    "target": "postgresql://usuario:contraseña@servidor-destino:5432/basedatos?sslmode=require",
    "options": ["--drop-if-exists", "--jobs", "4"]
  }'
```

Este comando devolverá una respuesta con un identificador de trabajo (job_id):

```json
{
  "job_id": "1234abcd-5678-90ef-ghij-klmn1234abcd",
  "status": "running",
  "command": "pgcopydb clone --source \"postgresql://...\" --target \"postgresql://...\" --drop-if-exists --jobs 4",
  "finished": false
}
```

Guarde el `job_id` para consultar el estado posteriormente.

### 2. Verificar el estado de un trabajo

```bash
curl http://localhost:8000/check-status/1234abcd-5678-90ef-ghij-klmn1234abcd
```

### 3. Ver los logs detallados de un trabajo específico

```bash
curl http://localhost:8000/logs/1234abcd-5678-90ef-ghij-klmn1234abcd
```

### 4. Ver el historial de todos los trabajos ejecutados

```bash
curl http://localhost:8000/execution-logs
```

### 5. Acceder a la documentación Swagger de la API

Abra en su navegador: http://localhost:8000/docs

### 6. Monitorear los logs directamente desde el contenedor

```bash
# Ver logs del contenedor pgcopydb
docker logs -f pgcopydb-container

# Ver logs del contenedor de la API
docker logs -f pgcopydb-api-container
```

## Operaciones Adicionales

### Realizar un dump de una base de datos

```bash
curl -X POST http://localhost:8000/dump \
  -H "Content-Type: application/json" \
  -d '{
    "source": "postgresql://usuario:contraseña@servidor:5432/basedatos?sslmode=require",
    "dir": "/app/pgcopydb_files/backups/mi_backup",
    "schema_only": false,
    "data_only": false
  }'
```

### Restaurar una base de datos desde un dump

```bash
curl -X POST http://localhost:8000/restore \
  -H "Content-Type: application/json" \
  -d '{
    "target": "postgresql://usuario:contraseña@servidor:5432/basedatos_nueva?sslmode=require",
    "dir": "/app/pgcopydb_files/backups/mi_backup"
  }'
```

### Copiar tablas específicas entre bases de datos

```bash
curl -X POST http://localhost:8000/copy \
  -H "Content-Type: application/json" \
  -d '{
    "source": "postgresql://usuario:contraseña@servidor-origen:5432/basedatos?sslmode=require",
    "target": "postgresql://usuario:contraseña@servidor-destino:5432/basedatos?sslmode=require",
    "tables": ["tabla1", "tabla2", "esquema.tabla3"]
  }'
```

### Listar tablas de una base de datos

```bash
curl -X POST http://localhost:8000/list-tables \
  -H "Content-Type: application/json" \
  -d '{
    "connection_string": "postgresql://usuario:contraseña@servidor:5432/basedatos?sslmode=require"
  }'
```

## Consideraciones de Seguridad

- **Protección de credenciales**: En un entorno de producción, no incluya contraseñas directamente en los comandos o en el código fuente. Utilice Azure Key Vault para almacenar secretos o variables de entorno seguras.
- **Acceso a la API**: Configure correctamente CORS y autenticación en la API antes de exponerla fuera de su entorno local.
- **Usuarios no-root**: Los contenedores utilizan usuarios no-root para mejorar la seguridad.

## Limpieza

Para detener y eliminar todos los recursos creados:

```bash
# Detener los contenedores
docker stop pgcopydb-container pgcopydb-api-container

# Eliminar los contenedores
docker rm pgcopydb-container pgcopydb-api-container

# Eliminar la red
docker network rm pgcopydb-network

# Eliminar el volumen (¡cuidado! esto eliminará los datos persistentes)
docker volume rm pgcopydb-data
```

## Preparación para Despliegue en AKS

Para implementar esta solución en Azure Kubernetes Service, consulte los archivos en el directorio `k8s/` y el chart de Helm en `pgcopydb-aks/`.

---

Última actualización: 9 de abril de 2025
