# Product Requirements Document: OpenShift ServiceAccount Kubeconfig Generator

## 📌 Overview

This application enables authenticated OpenShift users to generate and download kubeconfig files for newly created ServiceAccounts. It automates ServiceAccount creation, permission assignment, token generation, and kubeconfig construction. The application is deployed within the OpenShift cluster and interacts with the Kubernetes API using an in-cluster service account.

---

## 🎯 Goals

- Allow users to:
  - Select a namespace (or default to one)
  - Create a ServiceAccount
  - Assign one or more predefined RBAC roles
  - Generate a token with optional duration
  - Download a kubeconfig file ready for use with `kubectl` or `oc`
- Provide a secure, user-friendly web interface and API
- Operate entirely within the OpenShift cluster

---

## 👥 Target Users

- DevOps engineers, platform engineers, or developers
- External tools/pipelines needing service-level access to the cluster
- Internal operators needing limited-access kubeconfigs

---

## 🛠️ Architecture

### Backend Service

- **Language:** Python (Flask)
- **Responsibilities:**
  - Interact with the Kubernetes API
  - Create ServiceAccounts
  - Generate tokens using OpenShift subresource (`/token`)
  - Construct and serve downloadable kubeconfig YAML
  - Optionally store generated configs in temporary Secrets

### Frontend Interface

- **Framework:** Static HTML/JS
- **Features:**
  - Form for:
    - Namespace selection
    - ServiceAccount name input
    - Role selection
    - Token duration input
  - Status/error reporting
  - Kubeconfig download button

---

## 🔐 Permissions & Access Control

### ServiceAccount (for app itself)

The app requires a ClusterRole with the following permissions:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kubeconfig-generator
rules:
- apiGroups: [""]
  resources: ["serviceaccounts", "secrets"]
  verbs: ["get", "create", "list"]
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["rolebindings", "clusterrolebindings"]
  verbs: ["create"]
- apiGroups: [""]
  resources: ["serviceaccounts/token"]
  verbs: ["create"]
```

ClusterRole should be assigned to the application's ServiceAccount using SecurityContextConstraint.

---

## 🧹 Kubeconfig Output Format

```yaml
apiVersion: v1
kind: Config
clusters:
- name: <cluster-name>
  cluster:
    server: <api-server-url>
    certificate-authority-data: <base64-encoded-ca>
users:
- name: <sa-name>
  user:
    token: <sa-token>
contexts:
- name: <sa-name>@<cluster-name>
  context:
    cluster: <cluster-name>
    user: <sa-name>
    namespace: <namespace>
current-context: <sa-name>@<cluster-name>
```

---

## 🧪 Non-Goals

- Not intended for creating kubeconfigs for human users
- Does not support token refresh or renewal
- Does not implement long-term kubeconfig storage

---

## ⚠️ Security Considerations

- Token durations should be configurable but limited
- RBAC role options must be pre-approved and restricted
- Kubeconfigs should only be served to the initiating user session
- Expiration or auto-cleanup of any stored data/secrets
- Optional OAuth/OIDC integration to authenticate users before accessing UI

---

## 🗂️ Deployment Considerations

- Packaged as an OpenShift-compatible container
- Can be deployed via Helm chart or Operator
- Uses in-cluster service account for access
- Accessible via OpenShift Route or Console Plugin (optional future enhancement)

---

## ✅ Success Criteria

- Users can generate a working kubeconfig within 1–2 minutes
- Generated kubeconfigs allow access only to assigned namespace and roles
- No persistent secrets or tokens are stored unless explicitly configured
- RBAC is enforced at the API level; users cannot escalate privileges

---

## 🚣️ Future Enhancements (Optional)

- Audit logging for generated credentials
- Kubeconfig QR code export
- Console Plugin integration
- Expiring download links
- Support for multiple clusters

