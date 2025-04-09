# PgCopyDB AKS Helm Chart

This Helm chart deploys PgCopyDB and its API to Azure Kubernetes Service (AKS) using the "advconreg" Azure Container Registry and "adv_aks" AKS cluster.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- Access to Azure Container Registry "advconreg"
- AKS cluster "adv_aks" configured
- Secret configured for pulling images from ACR

## Getting Started

### Preparing for Deployment

1. Connect to your AKS cluster:
   ```bash
   az aks get-credentials --resource-group <resource-group-name> --name adv_aks
   ```

2. Create a secret for ACR access (if not already done):
   ```bash
   # Create a service principal for ACR access
   SP_PASSWORD=$(az ad sp create-for-rbac --name http://acr-service-principal --scopes $(az acr show --name advconreg --query id --output tsv) --role acrpull --query password --output tsv)
   SP_APP_ID=$(az ad sp show --id http://acr-service-principal --query appId --output tsv)

   # Create Kubernetes secret
   kubectl create secret docker-registry acr-secret \
     --docker-server=advconreg.azurecr.io \
     --docker-username=$SP_APP_ID \
     --docker-password=$SP_PASSWORD
   ```

### Build and Push Docker Images to ACR

```bash
# Log in to ACR
az acr login --name advconreg

# Build and push pgcopydb image
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/app
az acr build --registry advconreg --image pgcopydb-custom:latest .

# Build and push API image
cd /Users/alfonsod/Desarrollo/pgcopydb-aks/api
az acr build --registry advconreg --image pgcopydb-api:latest .
```

### Installing the Chart

1. Make sure you have the Helm CLI installed:
   ```bash
   helm version
   ```

2. Install the chart:
   ```bash
   # From the helm directory
   cd /Users/alfonsod/Desarrollo/pgcopydb-aks/helm
   helm install pgcopydb-release ./pgcopydb-aks
   ```

3. For a custom installation with overridden values:
   ```bash
   helm install pgcopydb-release ./pgcopydb-aks --values custom-values.yaml
   ```

### Uninstalling the Chart

```bash
helm uninstall pgcopydb-release
```

## Configuration

The following table lists the configurable parameters of the chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `imagePullSecrets` | Image pull secrets | `[{"name": "acr-secret"}]` |
| `pgcopydb.replicaCount` | Number of pgcopydb replicas | `1` |
| `pgcopydb.image.repository` | PgCopyDB image repository | `advconreg.azurecr.io/pgcopydb-custom` |
| `pgcopydb.image.tag` | PgCopyDB image tag | `latest` |
| `pgcopydb.image.pullPolicy` | PgCopyDB image pull policy | `Always` |
| `pgcopydb.service.type` | PgCopyDB service type | `ClusterIP` |
| `pgcopydb.service.port` | PgCopyDB service port | `8080` |
| `pgcopydb.persistence.enabled` | Enable persistence for pgcopydb | `true` |
| `pgcopydb.persistence.storageClass` | Storage class for PVC | `azure-disk-standard-lrs` |
| `pgcopydb.persistence.accessMode` | PVC access mode | `ReadWriteOnce` |
| `pgcopydb.persistence.size` | PVC storage size | `2Gi` |
| `pgcopydb.resources` | PgCopyDB resource requirements | Memory and CPU limits |
| `pgcopydbApi.replicaCount` | Number of pgcopydb-api replicas | `1` |
| `pgcopydbApi.image.repository` | PgCopyDB API image repository | `advconreg.azurecr.io/pgcopydb-api` |
| `pgcopydbApi.image.tag` | PgCopyDB API image tag | `latest` |
| `pgcopydbApi.image.pullPolicy` | PgCopyDB API image pull policy | `Always` |
| `pgcopydbApi.service.type` | PgCopyDB API service type | `LoadBalancer` |
| `pgcopydbApi.service.port` | PgCopyDB API service port | `80` |
| `pgcopydbApi.service.targetPort` | PgCopyDB API container port | `8000` |
| `pgcopydbApi.resources` | PgCopyDB API resource requirements | Memory and CPU limits |
| `pgcopydbApi.readinessProbe.periodSeconds` | Readiness probe interval | `10` |

## Storage Configuration

This chart is configured to use the most affordable Azure storage option for the proof of concept:

```yaml
pgcopydb:
  persistence:
    enabled: true
    storageClass: "azure-disk-standard-lrs"
    accessMode: ReadWriteOnce
    size: 2Gi
```

Azure Standard HDD managed disks (azure-disk-standard-lrs) provide cost-effective storage for the proof of concept.

## Examples

### Scaling Replicas

```yaml
# custom-values.yaml
pgcopydbApi:
  replicaCount: 3

pgcopydb:
  replicaCount: 2
```

Then apply with:

```bash
helm upgrade pgcopydb-release ./pgcopydb-aks --values custom-values.yaml
```

### Changing Service Types

```yaml
# custom-values.yaml
pgcopydbApi:
  service:
    type: ClusterIP
```

### Increasing Storage Size

```yaml
# custom-values.yaml
pgcopydb:
  persistence:
    size: 10Gi
```

## Accessing the API

Once deployed, you can access the API using:

```bash
# Get the external IP of the API service
export SERVICE_IP=$(kubectl get svc pgcopydb-aks-api-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "API is available at: http://$SERVICE_IP:80"

# Test the health endpoint
curl http://$SERVICE_IP:80/health
```

## Troubleshooting

1. Check the deployed resources:
   ```bash
   kubectl get all -l app.kubernetes.io/instance=pgcopydb-release
   ```

2. Check the pod logs:
   ```bash
   kubectl logs -l app=pgcopydb-api
   kubectl logs -l app=pgcopydb
   ```

3. Describe a pod for detailed information:
   ```bash
   kubectl describe pod -l app=pgcopydb-api
   ```

4. Check persistent volume claims:
   ```bash
   kubectl get pvc
   ```

5. If there are issues with image pulling:
   ```bash
   # Verify the secret exists
   kubectl get secret acr-secret
   
   # Check pod events
   kubectl get events --sort-by='.lastTimestamp'
   ```