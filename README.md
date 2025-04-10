# PgCopyDB para Azure Kubernetes Service (AKS)

Solución para clonar, migrar y manipular bases de datos PostgreSQL utilizando [pgcopydb](https://github.com/dimitri/pgcopydb) en contenedores Docker y Kubernetes.

## 📋 Índice

- [Descripción General](#descripción-general)
- [Componentes](#componentes)
- [Flujos Automatizados con GitHub Actions](#flujos-automatizados-con-github-actions)
- [Despliegue en AKS](#despliegue-en-aks)
- [Despliegue Local con Docker](#despliegue-local-con-docker)
- [Uso de la API](#uso-de-la-api)
- [Operaciones Disponibles](#operaciones-disponibles)
- [Monitorización y Logs](#monitorización-y-logs)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Consideraciones de Seguridad](#consideraciones-de-seguridad)
- [Resolución de Problemas](#resolución-de-problemas)
- [Limpieza de Recursos](#limpieza-de-recursos)

## 📝 Descripción General

PgCopyDB para AKS es una solución para implementar la herramienta [pgcopydb](https://github.com/dimitri/pgcopydb) en entornos containerizados. Permite clonar, migrar y gestionar bases de datos PostgreSQL de manera eficiente y escalable, con soporte para PostgreSQL 17.

## 🧩 Componentes

- **Contenedor PgCopyDB**: Versión containerizada de pgcopydb con soporte para PostgreSQL 17
- **API REST**: Interfaz para interactuar con pgcopydb de forma programática
- **Charts de Helm**:
  - `pgcopydb-aks`: Despliegue combinado de todos los componentes
  - `pgcopydb-api`: Despliegue exclusivo de la API
  - `pgcopydb-app`: Despliegue exclusivo de la aplicación pgcopydb

## 🔄 Flujos Automatizados con GitHub Actions

El proyecto incluye flujos de trabajo automatizados para CI/CD:

### 1. Construcción y Publicación de Imágenes Docker

Flujo de trabajo: `.github/workflows/docker-build.yml`

Este flujo se activa automáticamente en:
- Push a la rama principal
- Pull requests hacia la rama principal
- Activación manual desde GitHub

Operaciones:
- Compilación de imágenes Docker para pgcopydb y la API
- Análisis de seguridad de las imágenes
- Publicación en Azure Container Registry

### 2. Despliegue en AKS

Flujo de trabajo: `.github/workflows/deploy-to-aks.yml`

Este flujo se activa:
- Automáticamente después de una construcción exitosa de las imágenes
- Manualmente desde GitHub

Operaciones:
- Autenticación en Azure
- Conexión al clúster AKS
- Despliegue mediante Helm
- Verificación del estado del despliegue

## 🚀 Despliegue en AKS

### Requisitos previos

- Azure CLI instalado y configurado
- kubectl instalado y configurado
- Helm 3.x instalado
- Acceso a un Azure Container Registry (ACR)
- Un clúster AKS desplegado

### Pasos para el despliegue manual

1. **Iniciar sesión en Azure**

```bash
az login
```

2. **Conectarse al clúster AKS**

```bash
az aks get-credentials --resource-group <nombre-grupo-recursos> --name <nombre-cluster>
```

3. **Configurar acceso a ACR**

```bash
# Crear un service principal para ACR
SP_PASSWORD=$(az ad sp create-for-rbac --name http://acr-service-principal --scopes $(az acr show --name <nombre-acr> --query id --output tsv) --role acrpull --query password --output tsv)
SP_APP_ID=$(az ad sp show --id http://acr-service-principal --query appId --output tsv)

# Crear secreto en Kubernetes
kubectl create secret docker-registry acr-secret \
  --docker-server=<nombre-acr>.azurecr.io \
  --docker-username=$SP_APP_ID \
  --docker-password=$SP_PASSWORD
```

4. **Desplegar con Helm**

```bash
# Despliegue completo
helm install pgcopydb-release ./helm/pgcopydb-aks

# Con configuración personalizada
helm install pgcopydb-release ./helm/pgcopydb-aks -f custom-values.yaml

# Sólo componente API
helm install pgcopydb-api-release ./helm/pgcopydb-api

# Sólo componente pgcopydb
helm install pgcopydb-app-release ./helm/pgcopydb-app
```

5. **Verificar el despliegue**

```bash
kubectl get pods
kubectl get services
```

## 🐳 Despliegue Local con Docker

Para ejecutar el sistema localmente:

1. **Construir las imágenes Docker**

```bash
# Construir imagen pgcopydb
docker build -t pgcopydb-local:latest ./app

# Construir imagen API
docker build -t pgcopydb-api-local:latest ./api
```

2. **Crear recursos de red y almacenamiento**

```bash
docker network create pgcopydb-network
docker volume create pgcopydb-data
```

3. **Iniciar contenedores**

```bash
# Contenedor pgcopydb
docker run -d --name pgcopydb-container \
  --network pgcopydb-network \
  -v pgcopydb-data:/app/pgcopydb_files \
  pgcopydb-local:latest

# Contenedor API
docker run -d --name pgcopydb-api-container \
  --network pgcopydb-network \
  -p 8000:8000 \
  -v pgcopydb-data:/app/pgcopydb_files \
  pgcopydb-api-local:latest
```

## 🔌 Uso de la API

### Acceso a la API en AKS

```bash
# Obtener la IP externa del servicio
export SERVICE_IP=$(kubectl get svc pgcopydb-api -n pgcopydb -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "IP del servicio: $SERVICE_IP"

# Verificar estado
curl http://$SERVICE_IP:80/health

# Documentación Swagger
echo "Documentación disponible en: http://$SERVICE_IP:80/docs"
```

### Acceso Local

- API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/docs

## 🛠️ Operaciones Disponibles

### Clonar una base de datos

```bash
curl -X POST http://<api-endpoint>/clone \
  -H "Content-Type: application/json" \
  -d '{
    "source": "postgresql://usuario:contraseña@origen:5432/db?sslmode=require",
    "target": "postgresql://usuario:contraseña@destino:5432/db?sslmode=require",
    "options": ["--drop-if-exists", "--jobs", "4"]
  }'
```

### Otras operaciones

- **Realizar dump**: `POST /dump`
- **Restaurar desde dump**: `POST /restore`
- **Copiar tablas específicas**: `POST /copy`
- **Listar tablas**: `POST /list-tables`
- **Verificar estado**: `GET /check-status/{job_id}`
- **Ver logs**: `GET /logs/{job_id}`

Consulte la documentación Swagger para detalles completos.

## 📊 Monitorización y Logs

### En AKS

```bash
# Ver logs de los pods
kubectl logs -l app=pgcopydb-api
kubectl logs -l app=pgcopydb

# Monitorización detallada
kubectl describe pod -l app=pgcopydb-api
kubectl describe pod -l app=pgcopydb
```

### En Docker local

```bash
# Ver logs en tiempo real
docker logs -f pgcopydb-container
docker logs -f pgcopydb-api-container
```

## 📁 Estructura del Proyecto

```
pgcopydb-aks/
├── .github/workflows/       # Flujos de trabajo de GitHub Actions
├── api/                     # API REST (FastAPI)
├── app/                     # Aplicación pgcopydb
├── backup/                  # Directorio para backups
├── helm/                    # Charts de Helm
│   ├── pgcopydb-aks/        # Chart completo
│   ├── pgcopydb-api/        # Chart API
│   └── pgcopydb-app/        # Chart pgcopydb
└── k8s/                     # Manifiestos Kubernetes
```

## 🔒 Consideraciones de Seguridad

- **Gestión de credenciales**: Use Azure Key Vault para secretos, no hardcodee contraseñas
- **Control de acceso**: Configure autenticación y CORS en entornos de producción
- **Contenedores no-root**: Las imágenes Docker utilizan usuarios no-root
- **Network Policies**: Restrinja la comunicación entre pods en AKS
- **Escaneo de vulnerabilidades**: Automatizado en el flujo CI/CD

## ⚠️ Resolución de Problemas

1. **Problemas de conexión a la base de datos**
   - Verifique las credenciales y la conectividad a PostgreSQL
   - Asegúrese de que los firewalls permitan la conexión

2. **Errores en los pods**
   - Revise los logs: `kubectl logs -l app=pgcopydb-api`
   - Verifique la configuración: `kubectl describe pod -l app=pgcopydb-api`

3. **Problemas de almacenamiento**
   - Compruebe que el PVC está correctamente aprovisionado
   - Verifique los permisos de escritura en el volumen

## 🧹 Limpieza de Recursos

### En AKS

```bash
# Eliminar despliegue Helm
helm uninstall pgcopydb-release
```

### En Docker local

```bash
# Detener y eliminar contenedores
docker stop pgcopydb-container pgcopydb-api-container
docker rm pgcopydb-container pgcopydb-api-container

# Eliminar recursos de red y almacenamiento
docker network rm pgcopydb-network
docker volume rm pgcopydb-data
```

---

Última actualización: 10 de abril de 2025
