# Guía de Despliegue de Helm Charts para PgCopyDB en AKS

Este documento proporciona instrucciones detalladas para desplegar los diferentes Helm charts de PgCopyDB en Azure Kubernetes Service (AKS).

## Prerequisitos

- Kubernetes 1.19+
- Helm 3.2.0+
- Azure CLI configurado
- Acceso a un clúster AKS
- Acceso a un Azure Container Registry (ACR)

## Preparación del Entorno

### 1. Conectarse al clúster AKS

```bash
# Iniciar sesión en Azure
az login

# Conectarse al clúster AKS
az aks get-credentials --resource-group <nombre-grupo-recursos> --name <nombre-cluster>

# Verificar conexión
kubectl get nodes
```

### 2. Configurar acceso al Azure Container Registry

```bash
# Crear un principio de servicio para acceso al ACR
SP_PASSWORD=$(az ad sp create-for-rbac --name http://acr-service-principal --scopes $(az acr show --name <nombre-acr> --query id --output tsv) --role acrpull --query password --output tsv)
SP_APP_ID=$(az ad sp show --id http://acr-service-principal --query appId --output tsv)

# Crear secreto de Kubernetes para el ACR
kubectl create secret docker-registry acr-secret \
  --docker-server=<nombre-acr>.azurecr.io \
  --docker-username=$SP_APP_ID \
  --docker-password=$SP_PASSWORD
```

### 3. Construir y subir imágenes Docker al ACR

```bash
# Iniciar sesión en el ACR
az acr login --name <nombre-acr>

# Construir y subir imagen de pgcopydb
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/app
az acr build --registry <nombre-acr> --image pgcopydb-custom:latest .

# Construir y subir imagen de la API
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/api
az acr build --registry <nombre-acr> --image pgcopydb-api:latest .
```

## Opciones de Despliegue

Este proyecto ofrece tres opciones de despliegue utilizando Helm:

1. **Despliegue Completo**: Despliega tanto la API como la aplicación pgcopydb.
2. **Solo API**: Despliega únicamente el componente de la API REST.
3. **Solo Aplicación**: Despliega únicamente el componente de la aplicación pgcopydb.

## 1. Despliegue Completo con pgcopydb-aks

Este chart despliega tanto la API como la aplicación pgcopydb juntos.

### Instalación Básica

```bash
# Navegar al directorio de Helm
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/helm

# Instalar el chart
helm install pgcopydb-release ./pgcopydb-aks
```

### Instalación con Valores Personalizados

1. Crear un archivo `custom-values.yaml` con las configuraciones personalizadas:

```yaml
# Ejemplo de custom-values.yaml
pgcopydb:
  replicaCount: 2
  persistence:
    size: 5Gi
  
pgcopydbApi:
  replicaCount: 3
  service:
    type: LoadBalancer
```

2. Instalar el chart con los valores personalizados:

```bash
helm install pgcopydb-release ./pgcopydb-aks -f custom-values.yaml
```

### Verificar el Despliegue

```bash
# Verificar que todos los pods estén en ejecución
kubectl get pods -l "app.kubernetes.io/instance=pgcopydb-release"

# Obtener la dirección IP externa de la API
export SERVICE_IP=$(kubectl get svc pgcopydb-aks-api-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "API disponible en: http://$SERVICE_IP:80"

# Probar la API
curl http://$SERVICE_IP:80/health
```

### Actualizar el Despliegue

```bash
# Editar los valores personalizados y actualizar
helm upgrade pgcopydb-release ./pgcopydb-aks -f custom-values.yaml
```

### Desinstalar el Despliegue

```bash
helm uninstall pgcopydb-release
```

## 2. Despliegue de Solo API con pgcopydb-api

Este chart despliega únicamente el componente de la API REST.

### Instalación Básica

```bash
# Navegar al directorio de Helm
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/helm

# Instalar el chart
helm install pgcopydb-api-release ./pgcopydb-api
```

### Instalación con Valores Personalizados

1. Crear un archivo `api-values.yaml` con las configuraciones personalizadas:

```yaml
# Ejemplo de api-values.yaml
replicaCount: 2
image:
  repository: <nombre-acr>.azurecr.io/pgcopydb-api
  tag: latest
service:
  type: LoadBalancer
  port: 80
resources:
  limits:
    cpu: "1"
    memory: "1Gi"
  requests:
    cpu: "500m"
    memory: "512Mi"
```

2. Instalar el chart con los valores personalizados:

```bash
helm install pgcopydb-api-release ./pgcopydb-api -f api-values.yaml
```

### Verificar el Despliegue

```bash
# Verificar que los pods de la API estén en ejecución
kubectl get pods -l "app.kubernetes.io/instance=pgcopydb-api-release"

# Obtener la dirección IP externa de la API
export API_IP=$(kubectl get svc pgcopydb-api-release -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "API disponible en: http://$API_IP:80"

# Probar la API
curl http://$API_IP:80/health
```

### Desinstalar el Despliegue

```bash
helm uninstall pgcopydb-api-release
```

## 3. Despliegue de Solo Aplicación con pgcopydb-app

Este chart despliega únicamente el componente de la aplicación pgcopydb.

### Instalación Básica

```bash
# Navegar al directorio de Helm
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/helm

# Instalar el chart
helm install pgcopydb-app-release ./pgcopydb-app
```

### Instalación con Valores Personalizados

1. Crear un archivo `app-values.yaml` con las configuraciones personalizadas:

```yaml
# Ejemplo de app-values.yaml
replicaCount: 1
image:
  repository: <nombre-acr>.azurecr.io/pgcopydb-custom
  tag: latest
persistence:
  enabled: true
  storageClass: "managed-premium"
  size: 10Gi
resources:
  limits:
    cpu: "2"
    memory: "4Gi"
  requests:
    cpu: "1"
    memory: "2Gi"
```

2. Instalar el chart con los valores personalizados:

```bash
helm install pgcopydb-app-release ./pgcopydb-app -f app-values.yaml
```

### Verificar el Despliegue

```bash
# Verificar que los pods de pgcopydb estén en ejecución
kubectl get pods -l "app.kubernetes.io/instance=pgcopydb-app-release"

# Verificar que el PVC se haya creado correctamente
kubectl get pvc -l "app.kubernetes.io/instance=pgcopydb-app-release"
```

### Desinstalar el Despliegue

```bash
helm uninstall pgcopydb-app-release
```

## Recomendaciones de Seguridad para AKS

- Utilizar siempre identidades administradas para autenticación cuando sea posible
- No codificar credenciales en los archivos de valores, usar secretos de Kubernetes
- Configurar reglas de red adecuadas para limitar el acceso a los servicios
- Mantener actualizadas las imágenes y los charts de Helm
- Utilizar Network Policies para restringir el tráfico entre pods
- Implementar RBAC para controlar el acceso al clúster y a los recursos

## Solución de Problemas

### Problemas con Permisos de Acceso al ACR

```bash
# Verificar que el secreto existe
kubectl get secret acr-secret

# Verificar eventos de Kubernetes
kubectl get events --sort-by='.lastTimestamp'

# Revisar los logs de los pods
kubectl logs <nombre-pod>
```

### Problemas con Persistent Volume Claims

```bash
# Verificar el estado de los PVCs
kubectl get pvc

# Verificar los detalles del PVC
kubectl describe pvc <nombre-pvc>
```

### Problemas con la API

```bash
# Revisar los logs de la API
kubectl logs -l app=pgcopydb-api

# Verificar la configuración del servicio
kubectl describe service pgcopydb-aks-api-service
```

---

*Última actualización: 10 de abril de 2025*
