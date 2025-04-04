# pgcopydb-aks: API REST para pgcopydb en Azure Kubernetes Service

Este proyecto implementa pgcopydb como un microservicio en Azure Kubernetes Service (AKS), exponiendo sus funcionalidades a través de una API REST desarrollada con FastAPI.

## Descripción

pgcopydb es una herramienta de línea de comandos que permite clonar, volcar y restaurar bases de datos PostgreSQL. Este proyecto la convierte en un servicio REST para facilitar su integración en flujos automatizados.

## Estructura del Proyecto

```
pgcopydb-aks/
├── api/                    # Código de la API REST (FastAPI)
│   ├── Dockerfile          # Dockerfile para la imagen de la API
│   ├── main.py             # Código principal de la API FastAPI
│   └── requirements.txt    # Dependencias de Python
├── k8s/                    # Manifiestos de Kubernetes
│   ├── pgcopydb-deployment.yaml       # Despliegue de pgcopydb
│   ├── pgcopydb-api-deployment.yaml   # Despliegue de la API
│   └── pgcopydb-api-service.yaml      # Servicio para exponer la API
├── scripts/                # Scripts de utilidad para pgcopydb
├── Dockerfile              # Dockerfile para la imagen base pgcopydb
└── README.md               # Este archivo
```

## Requisitos Previos

- Azure CLI instalado
- kubectl configurado para AKS
- Docker instalado
- Acceso a un Azure Container Registry (ACR)
- Un clúster AKS configurado

## Instrucciones de Despliegue

### 1. Construir y Publicar Imágenes Docker

#### Imagen base de pgcopydb

```bash
# Crear carpeta para scripts (si no existe)
mkdir -p scripts

# Construir la imagen
docker build -t pgcopydb-custom .

# Etiquetar y publicar en ACR
az acr login --name <tu-acr-name>
docker tag pgcopydb-custom <tu-acr-name>.azurecr.io/pgcopydb-custom:latest
docker push <tu-acr-name>.azurecr.io/pgcopydb-custom:latest
```

#### Imagen de la API FastAPI

```bash
# Construir la imagen
docker build -t pgcopydb-api -f api/Dockerfile api/

# Etiquetar y publicar en ACR
docker tag pgcopydb-api <tu-acr-name>.azurecr.io/pgcopydb-api:latest
docker push <tu-acr-name>.azurecr.io/pgcopydb-api:latest
```

### 2. Actualizar los manifiestos de Kubernetes

Editar los archivos YAML en la carpeta `k8s/` para reemplazar `<tu-acr-name>` con el nombre real de tu Azure Container Registry.

### 3. Desplegar en AKS

```bash
# Asegurarse de que kubectl está configurado para el clúster AKS correcto
az aks get-credentials --resource-group <resource-group> --name <aks-cluster-name>

# Desplegar pgcopydb
kubectl apply -f k8s/pgcopydb-deployment.yaml

# Desplegar la API y el servicio
kubectl apply -f k8s/pgcopydb-api-deployment.yaml
kubectl apply -f k8s/pgcopydb-api-service.yaml
```

### 4. Verificar el Despliegue

```bash
# Comprobar que los pods están en ejecución
kubectl get pods

# Obtener la IP pública del servicio API
kubectl get service pgcopydb-api-service
```

## Uso de la API

Una vez desplegada, puedes acceder a la documentación interactiva de la API navegando a:

```
http://<IP_PUBLICA>/docs
```

### Endpoints Disponibles

#### Clonar Base de Datos

```bash
curl -X POST "http://<IP_PUBLICA>/clone" \
     -H "Content-Type: application/json" \
     -d '{"source":"postgres://user:pass@host1/db1", "target":"postgres://user:pass@host2/db2"}'
```

#### Realizar un Dump

```bash
curl -X POST "http://<IP_PUBLICA>/dump" \
     -H "Content-Type: application/json" \
     -d '{"source":"postgres://user:pass@host/db", "dir":"/path/to/dump/dir"}'
```

#### Restaurar Base de Datos

```bash
curl -X POST "http://<IP_PUBLICA>/restore" \
     -H "Content-Type: application/json" \
     -d '{"target":"postgres://user:pass@host/db", "dir":"/path/to/dump/dir"}'
```

## Monitorización y Logs

### Ver logs de la API

```bash
# Obtener el nombre del pod
kubectl get pods

# Ver logs en tiempo real
kubectl logs -f <nombre-del-pod-api>
```

### Ver logs de pgcopydb

```bash
kubectl logs -f <nombre-del-pod-pgcopydb>
```

## Solución de Problemas

### Problemas de Comunicación entre Servicios

Si la API no puede comunicarse con pgcopydb, verifica:

1. Que ambos pods estén en ejecución: `kubectl get pods`
2. Los logs de los pods para detectar errores: `kubectl logs <pod-name>`
3. La configuración de red del clúster

### Errores en la Ejecución de Comandos pgcopydb

Los detalles de los errores son devueltos en la respuesta de la API. Consulta la documentación de pgcopydb para entender los mensajes de error específicos:
[Documentación de pgcopydb](https://pgcopydb.readthedocs.io/)

## Mantenimiento

### Actualizar la Imagen de pgcopydb

```bash
docker build -t <tu-acr-name>.azurecr.io/pgcopydb-custom:latest .
docker push <tu-acr-name>.azurecr.io/pgcopydb-custom:latest
kubectl rollout restart deployment pgcopydb
```

### Actualizar la API

```bash
docker build -t <tu-acr-name>.azurecr.io/pgcopydb-api:latest -f api/Dockerfile api/
docker push <tu-acr-name>.azurecr.io/pgcopydb-api:latest
kubectl rollout restart deployment pgcopydb-api
```

## Referencias

- [pgcopydb Documentation](https://pgcopydb.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Kubernetes Service Documentation](https://docs.microsoft.com/en-us/azure/aks/)
