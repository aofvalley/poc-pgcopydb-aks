# PgCopyDB AKS Helm Chart

This Helm chart deploys PgCopyDB and its API to an Azure Kubernetes Service (AKS) cluster.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- Access to an Azure Container Registry (ACR)
- AKS secret configured for pulling images from ACR

## Getting Started

### Installing the Chart

1. Make sure you have the Helm CLI installed:
   ```bash
   helm version
   ```

2. Install the chart:
   ```bash
   # From the project root directory
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
| `pgcopydb.resources` | PgCopyDB resource requirements | Memory and CPU limits |
| `pgcopydbApi.replicaCount` | Number of pgcopydb-api replicas | `1` |
| `pgcopydbApi.image.repository` | PgCopyDB API image repository | `advconreg.azurecr.io/pgcopydb-api` |
| `pgcopydbApi.image.tag` | PgCopyDB API image tag | `latest` |
| `pgcopydbApi.image.pullPolicy` | PgCopyDB API image pull policy | `Always` |
| `pgcopydbApi.service.type` | PgCopyDB API service type | `LoadBalancer` |
| `pgcopydbApi.service.port` | PgCopyDB API service port | `80` |
| `pgcopydbApi.resources` | PgCopyDB API resource requirements | Memory and CPU limits |

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