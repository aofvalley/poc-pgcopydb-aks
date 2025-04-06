# pgcopydb-aks: API REST para pgcopydb en Azure Kubernetes Service

Este proyecto implementa pgcopydb como un microservicio en Azure Kubernetes Service (AKS), exponiendo sus funcionalidades a través de una API REST desarrollada con FastAPI. El proyecto es compatible con PostgreSQL Flexible Server versión 17.

## Descripción

pgcopydb es una herramienta de línea de comandos que permite clonar, volcar y restaurar bases de datos PostgreSQL. Este proyecto la convierte en un servicio REST para facilitar su integración en flujos automatizados.

## Estructura del Proyecto

```
pgcopydb-aks/
├── api/                    # Código de la API REST (FastAPI)
│   ├── Dockerfile          # Dockerfile para la imagen de la API
│   ├── main.py             # Código principal de la API FastAPI
│   └── requirements.txt    # Dependencias de Python
├── app/                    # Aplicación pgcopydb
│   └── Dockerfile          # Dockerfile para la imagen de pgcopydb
├── backup/                 # Directorio para almacenar backups
│   └── pgcopydb/           # Backups de pgcopydb
├── k8s/                    # Manifiestos de Kubernetes
│   ├── pgcopydb-deployment.yaml       # Despliegue de pgcopydb
│   ├── pgcopydb-api-deployment.yaml   # Despliegue de la API
│   └── pgcopydb-api-service.yaml      # Servicio para exponer la API
├── pgcopydb-aks/           # Helm chart para despliegue en AKS
│   ├── Chart.yaml          # Metadatos del chart
│   ├── values.yaml         # Valores por defecto del chart
│   └── templates/          # Plantillas del chart
└── README.md               # Este archivo
```

## Requisitos Previos

- Docker instalado para ejecución local
- Azure CLI instalado para despliegue en AKS
- kubectl configurado para AKS
- Acceso a un Azure Container Registry (ACR)
- Un clúster AKS configurado

### Instalación de Azure CLI

Si no tienes Azure CLI instalado, sigue estos pasos:

1. **macOS**:
   ```bash
   brew install azure-cli
   ```

2. **Linux**:
   ```bash
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

3. **Windows**:
   Descarga el instalador desde [Azure CLI](https://aka.ms/installazurecliwindows).

4. Verifica la instalación:
   ```bash
   az --version
   ```

## Ejecución en Docker Local

### 1. Construir las imágenes Docker

#### Imagen de pgcopydb con soporte para PostgreSQL 17

```bash
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/app
docker build -t pgcopydb-pg17:latest .
```

#### Imagen de la API FastAPI

```bash
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/api
docker build -t pgcopydb-api:latest .
```

### 2. Crear directorios para backups

```bash
mkdir -p ~/backups/pgcopydb
```

### 3. Crear una red Docker para comunicación entre contenedores

```bash
docker network create pgcopydb-network
```

### 4. Ejecutar el contenedor de pgcopydb

```bash
docker run --rm -d \
  --name pgcopydb-container \
  --network pgcopydb-network \
  -v ~/backups/pgcopydb:/app/backups \
  pgcopydb-pg17:latest \
  tail -f /dev/null
```

### 5. Ejecutar el contenedor de la API

```bash
docker run --rm -d \
  --name pgcopydb-api-container \
  --network pgcopydb-network \
  -p 8000:8000 \
  -v ~/backups/pgcopydb:/app/backups \
  pgcopydb-api:latest
```

### 6. Verificar que los contenedores están en ejecución

```bash
docker ps
```

### 7. Uso de pgcopydb desde el contenedor

Para ejecutar comandos directamente en el contenedor de pgcopydb:

```bash
docker exec pgcopydb-container \
  pgcopydb dump schema \
  --source "postgresql://advpsqlfxuk.postgres.database.azure.com:5432/postgres?user=alfonsod&password=Raulito09&sslmode=require" \
  --dir /app/backups/advpsqlfxuk-dump
```

### 8. Uso de la API para operaciones pgcopydb

La API estará disponible en `http://localhost:8000` con documentación interactiva en `http://localhost:8000/docs`.

#### Ejemplos de uso de la API

**Dump Schema específico para PostgreSQL 17 (endpoint predefinido):**
```bash
curl -X POST "http://localhost:8000/adv-dump-schema" \
     -H "accept: application/json"
```

**Dump Schema personalizado:**
```bash
curl -X POST "http://localhost:8000/dump-schema" \
     -H "Content-Type: application/json" \
     -d '{
       "source": "postgresql://usuario:contraseña@host:puerto/basedatos?sslmode=require",
       "dir": "/app/backups/mi-dump"
     }'
```

**Verificar estado de un trabajo:**
```bash
curl -X GET "http://localhost:8000/check-status/JOB_ID" \
     -H "accept: application/json"
```

## Despliegue en Azure Kubernetes Service (AKS)

### 1. Autenticarse en Azure y crear recursos necesarios

```bash
# Iniciar sesión en Azure
az login

# Crear un grupo de recursos (si no existe)
az group create --name myResourceGroup --location eastus

# Crear ACR (si no existe)
az acr create --resource-group myResourceGroup --name myacr --sku Basic

# Crear AKS (si no existe)
az aks create \
    --resource-group myResourceGroup \
    --name myAKSCluster \
    --node-count 2 \
    --enable-managed-identity \
    --attach-acr myacr \
    --generate-ssh-keys
```

### 2. Configurar kubectl para comunicarse con AKS

```bash
az aks get-credentials --resource-group myResourceGroup --name myAKSCluster
```

### 3. Construir y publicar imágenes Docker en ACR

```bash
# Iniciar sesión en ACR
az acr login --name myacr

# Construir y etiquetar la imagen de pgcopydb
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/app
docker build -t pgcopydb-pg17:latest .
docker tag pgcopydb-pg17:latest myacr.azurecr.io/pgcopydb-pg17:latest
docker push myacr.azurecr.io/pgcopydb-pg17:latest

# Construir y etiquetar la imagen de la API
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/api
docker build -t pgcopydb-api:latest .
docker tag pgcopydb-api:latest myacr.azurecr.io/pgcopydb-api:latest
docker push myacr.azurecr.io/pgcopydb-api:latest
```

### 4. Opciones de Despliegue en AKS

#### Opción A: Despliegue con manifiestos Kubernetes

Editar los archivos YAML en la carpeta `k8s/` para reemplazar las referencias de imagen con tus imágenes en ACR.

```bash
# Editar los manifiestos
# En pgcopydb-deployment.yaml, cambiar:
# image: pgcopydb-pg17:latest
# a: image: myacr.azurecr.io/pgcopydb-pg17:latest

# En pgcopydb-api-deployment.yaml, cambiar:
# image: pgcopydb-api:latest
# a: image: myacr.azurecr.io/pgcopydb-api:latest

# Aplicar los manifiestos
kubectl apply -f k8s/pgcopydb-deployment.yaml
kubectl apply -f k8s/pgcopydb-api-deployment.yaml
kubectl apply -f k8s/pgcopydb-api-service.yaml
```

#### Opción B: Despliegue con Helm Chart (Recomendado)

El proyecto incluye un Helm chart que facilita la configuración y despliegue.

1. **Personalizar valores** (crea un archivo `custom-values.yaml`):
   ```yaml
   # custom-values.yaml
   pgcopydb:
     image:
       repository: myacr.azurecr.io/pgcopydb-pg17
       tag: latest
     resources:
       limits:
         cpu: 1000m
         memory: 1Gi
       requests:
         cpu: 500m
         memory: 512Mi
   
   pgcopydbApi:
     image:
       repository: myacr.azurecr.io/pgcopydb-api
       tag: latest
     service:
       type: LoadBalancer
     resources:
       limits:
         cpu: 500m
         memory: 512Mi
       requests:
         cpu: 250m
         memory: 256Mi
   
   persistentVolume:
     enabled: true
     size: 10Gi
     storageClass: managed-premium
   ```

2. **Desplegar con Helm**:
   ```bash
   # Navegar al directorio del proyecto
   cd /Users/alfonsod/Desarrollo/pgcopydb-aks/
   
   # Instalar el chart
   helm install pgcopydb-release ./pgcopydb-aks --values custom-values.yaml
   
   # Verificar la instalación
   helm list
   kubectl get all -l app.kubernetes.io/instance=pgcopydb-release
   ```

3. **Actualizar el despliegue** (si hay cambios):
   ```bash
   helm upgrade pgcopydb-release ./pgcopydb-aks --values custom-values.yaml
   ```

4. **Desinstalar el chart**:
   ```bash
   helm uninstall pgcopydb-release
   ```

### 5. Verificar el Despliegue

```bash
# Verificar pods
kubectl get pods

# Verificar servicios y obtener la IP externa
kubectl get services
```

## Uso de pgcopydb con PostgreSQL 17 en Azure

La solución está optimizada para trabajar con PostgreSQL Flexible Server versión 17 en Azure. A continuación se muestran ejemplos específicos:

### Desde Docker local

```bash
# Ejecutar pgcopydb directamente desde el contenedor
docker exec pgcopydb-container \
  pgcopydb dump schema \
  --source "postgresql://advpsqlfxuk.postgres.database.azure.com:5432/postgres?user=alfonsod&password=Raulito09&sslmode=require" \
  --dir /app/backups/advpsqlfxuk-dump
```

### Desde la API REST

```bash
# Usar el endpoint predefinido
curl -X POST "http://localhost:8000/adv-dump-schema" \
     -H "accept: application/json"

# O usando el endpoint genérico
curl -X POST "http://localhost:8000/dump-schema" \
     -H "Content-Type: application/json" \
     -d '{
       "source": "postgresql://advpsqlfxuk.postgres.database.azure.com:5432/postgres?user=alfonsod&password=Raulito09&sslmode=require",
       "dir": "/app/backups/advpsqlfxuk-dump"
     }'
```

### Desde AKS

Una vez desplegado en AKS, puedes acceder a la API a través de la IP externa o nombre DNS asignado:

```bash
# Obtener la IP externa
kubectl get service pgcopydb-api-service

# Usar la API (reemplaza EXTERNAL-IP con la IP obtenida)
curl -X POST "http://EXTERNAL-IP:8000/adv-dump-schema" \
     -H "accept: application/json"
```

## Consideraciones de Seguridad en Azure

- **Credenciales**: No exponga credenciales en líneas de comandos o archivos de configuración públicos. Considere usar Azure Key Vault para almacenar secretos.
- **Managed Identity**: Cuando sea posible, configure Managed Identity para la autenticación entre servicios de Azure.
- **Reglas de Firewall**: Restrinja el acceso a su PostgreSQL Flexible Server mediante reglas de firewall adecuadas.
- **Cifrado**: Asegúrese de que todas las conexiones a PostgreSQL usen SSL/TLS mediante el parámetro `sslmode=require`.
- **RBAC en AKS**: Utilice el control de acceso basado en roles de Kubernetes para limitar los permisos.

## Monitorización y Solución de Problemas

### Verificar logs en Docker local

```bash
# Logs de pgcopydb
docker logs pgcopydb-container

# Logs de la API
docker logs pgcopydb-api-container
```

### Verificar logs en AKS

```bash
# Obtener nombres de los pods
kubectl get pods

# Logs de pgcopydb
kubectl logs -f <nombre-del-pod-pgcopydb>

# Logs de la API
kubectl logs -f <nombre-del-pod-api>
```

### Problemas comunes y soluciones

1. **Error de conexión a PostgreSQL**:
   - Verifique las credenciales y la cadena de conexión
   - Compruebe las reglas de firewall de Azure PostgreSQL
   - Verifique que el parámetro `sslmode=require` esté presente

2. **Error en pgcopydb**:
   - Verifique los logs para detalles específicos
   - Consulte la [documentación oficial de pgcopydb](https://pgcopydb.readthedocs.io/)

3. **Error al construir imágenes Docker**:
   - Asegúrese de utilizar la base Debian para compatibilidad con PostgreSQL 17
   - Verifique que tiene los permisos necesarios

## Referencias

- [pgcopydb Documentation](https://pgcopydb.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Kubernetes Service Documentation](https://docs.microsoft.com/en-us/azure/aks/)
- [Azure Container Registry Documentation](https://docs.microsoft.com/en-us/azure/container-registry/)
- [PostgreSQL Flexible Server Documentation](https://docs.microsoft.com/en-us/azure/postgresql/flexible-server/)

## Fecha de última actualización

6 de abril de 2025
