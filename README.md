# Kubegen - OpenShift ServiceAccount Kubeconfig Generator

A web application that enables authenticated OpenShift users to generate and download kubeconfig files for newly created ServiceAccounts. It automates ServiceAccount creation, permission assignment, token generation, and kubeconfig construction within the OpenShift cluster.

## 🎯 Features

- **Web Interface**: User-friendly HTML/JavaScript frontend
- **ServiceAccount Management**: Automatic creation of ServiceAccounts in selected namespaces
- **Token Generation**: Secure token generation with configurable duration
- **Kubeconfig Generation**: Complete kubeconfig files ready for use with `kubectl` or `oc`
- **RBAC Integration**: Uses in-cluster service account with proper permissions
- **Configurable**: Environment-specific configuration via ConfigMap

## 🏗️ Architecture

### Backend (Python/Flask)
- **Language**: Python 3.8+
- **Framework**: Flask
- **Dependencies**: `kubernetes`, `flask`
- **API Endpoints**:
  - `GET /api/namespaces` - List available namespaces
  - `POST /api/generate-kubeconfig` - Generate kubeconfig for ServiceAccount

### Frontend (Static HTML/JS)
- **Framework**: Vanilla JavaScript
- **Features**: Dynamic namespace dropdown, form validation, file download
- **Dependencies**: js-yaml (CDN) for YAML formatting

## 🚀 Quick Start

### Prerequisites
- OpenShift cluster access
- `oc` CLI tool
- Container build tools (Podman/Docker)

### 1. Build the Container Image

```bash
# Create namespace and buildconfig for publishing to local registry
oc apply -k build/base
```

### 2. Deploy to OpenShift

Use the [base confimap](deployment/base/configmap.yaml) example and revise it in an overlay.

```bash
# Apply the test overlay to deploy the application
oc apply -k deployment/overlays/test
```

### 3. Access the Application

```bash
# Get the route URL
oc get route kubeconfig-generator -n kubegen

# Or access directly
oc get route kubeconfig-generator -n kubegen -o jsonpath='{.spec.host}'
```

## ⚙️ Configuration

The application is configured via a ConfigMap with the following parameters:

### Cluster Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CLUSTER_NAME` | `"openshift"` | Name of the cluster in generated kubeconfig |
| `EXTERNAL_CLUSTER_URL` | `"https://api.your-cluster.example.com:6443"` | External API server URL (must be reachable from outside cluster) |

### Application Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FLASK_ENV` | `"production"` | Flask environment setting |
| `FLASK_DEBUG` | `"false"` | Enable Flask debug mode |
| `DEFAULT_TOKEN_DURATION` | `"3600"` | Default token duration in seconds (minimum 1 hour) |
| `LOG_LEVEL` | `"INFO"` | Application logging level |

### Updating Configuration

```bash
# Update external cluster URL
oc patch configmap kubegen-config -n kubegen --patch '{"data":{"EXTERNAL_CLUSTER_URL":"https://api.your-cluster.example.com:6443"}}'

# Update token duration
oc patch configmap kubegen-config -n kubegen --patch '{"data":{"DEFAULT_TOKEN_DURATION":"7200"}}'

# Restart deployment to pick up changes
oc rollout restart deployment/kubeconfig-generator -n kubegen
```

## 🔐 Security & Permissions

### Required RBAC Permissions

The application requires a ClusterRole with the following permissions:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kubeconfig-generator
rules:
- apiGroups: [""]
  resources: ["serviceaccounts", "namespaces"]
  verbs: ["get", "create", "list"]
- apiGroups: [""]
  resources: ["serviceaccounts/token"]
  verbs: ["create"]
- apiGroups: ["oauth.openshift.io"]
  resources: ["oauthaccesstokens"]
  verbs: ["create"]
```

### Security Considerations

- **Token Duration**: Configurable but limited to prevent long-lived credentials
- **Namespace Isolation**: ServiceAccounts are created in user-selected namespaces
- **No Persistent Storage**: Generated kubeconfigs are not stored
- **In-Cluster Access**: Application uses in-cluster service account authentication

## 📁 Project Structure

```
kubegen/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
├── frontend/             # Static frontend files
│   ├── index.html        # Main HTML page
│   ├── app.js           # JavaScript logic
│   └── style.css        # CSS styling
├── deployment/           # Kubernetes/OpenShift manifests
│   ├── base/            # Base Kustomize configuration
│   │   ├── namespace.yaml
│   │   ├── clusterrole.yaml
│   │   ├── clusterrolebinding.yaml
│   │   ├── configmap.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── route.yaml
│   │   ├── serviceaccount.yaml
│   │   └── kustomization.yaml
│   └── overlays/         # Environment-specific overlays
│       ├── test/
│       └── prod/
├── PRD.md               # Product Requirements Document
├── PLAN.md              # Development Plan
└── README.md            # This file
```

# TODO

RBAC for the service account

## 🔧 Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires kubeconfig)
export KUBECONFIG=~/.kube/config
python app.py
```

### Building for Different Architectures

```bash
# For x86_64 (OpenShift)
podman build --platform linux/amd64 -t kubegen .

# For ARM64 (Apple Silicon)
podman build --platform linux/arm64 -t kubegen .

# Multi-architecture
podman build --platform linux/amd64,linux/arm64 -t kubegen .
```

### Testing

```bash
# Test the API endpoints
curl http://localhost:8080/api/namespaces
curl -X POST http://localhost:8080/api/generate-kubeconfig \
  -H "Content-Type: application/json" \
  -d '{"namespace":"default","serviceAccountName":"test-sa","tokenDuration":3600}'
```

## 🐛 Troubleshooting

### Common Issues

1. **Empty Namespace Dropdown**
   - Check RBAC permissions
   - Verify ClusterRoleBinding namespace matches deployment namespace
   - Check application logs: `oc logs deployment/kubeconfig-generator -n kubegen`

2. **Token Generation Errors**
   - Ensure OpenShift Python client is installed
   - Verify service account has token creation permissions
   - Check token duration (minimum 1 hour)

3. **External URL Issues**
   - Verify `EXTERNAL_CLUSTER_URL` is reachable from outside cluster
   - Check DNS resolution and firewall rules
   - Ensure correct port (typically 6443)

### Debug Commands

```bash
# Check pod status
oc get pods -n kubegen

# View application logs
oc logs deployment/kubeconfig-generator -n kubegen -f

# Test API endpoint from within cluster
oc exec deployment/kubeconfig-generator -n kubegen -- curl -s http://localhost:8080/api/namespaces

# Check ConfigMap
oc get configmap kubegen-config -n kubegen -o yaml

# Verify RBAC
oc auth can-i list namespaces --as system:serviceaccount:kubegen:kubeconfig-generator
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review the logs for error details
