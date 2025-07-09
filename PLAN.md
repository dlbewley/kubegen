# Plan: OpenShift ServiceAccount Kubeconfig Generator

This document outlines the plan to build the OpenShift ServiceAccount Kubeconfig Generator application.

### Phase 1: Backend API (Python/Flask)

1.  **Project Setup:**
    *   Initialize a Python project with `pip` and `virtualenv`.
    *   Install Flask and the official Kubernetes Python client (`kubernetes`).
    *   Create a basic Flask application structure.

2.  **Kubernetes Integration:**
    *   Implement logic to load the in-cluster service account credentials, which will be used to authenticate with the Kubernetes API.
    *   Create a helper function to initialize the Kubernetes API client.

3.  **API Endpoints:**
    *   **`GET /api/namespaces`**:
        *   This endpoint will list all namespaces the application's service account has access to. For the first version, we'll assume the service account has broad read access to namespaces. The user will select from this list on the frontend.
    *   **`POST /api/generate-kubeconfig`**:
        *   Accepts `namespace`, `serviceAccountName`, and `tokenDuration` as JSON payload.
        *   **Logic:**
            1.  Check if a ServiceAccount with the given name already exists in the namespace. If not, create it.
            2.  Generate a service account token using the `create_namespaced_service_account_token` method. The token duration will be set here (minimum 1 hour).
            3.  Retrieve the cluster's API server URL and CA certificate data. This can be obtained from the in-cluster environment.
            4.  Construct the kubeconfig file in the specified YAML format using the retrieved data and the generated token.
            5.  Return the generated kubeconfig as a file download or a JSON response.

### Phase 2: Frontend (Static HTML/JS)

1.  **HTML Structure (`index.html`):**
    *   A simple HTML form with the following fields:
        *   A dropdown for `namespace`, which will be populated dynamically from the `/api/namespaces` endpoint.
        *   A text input for the `serviceAccountName`.
        *   A number input for `tokenDuration`, with a `min` attribute set to `3600` (1 hour in seconds).
    *   A button to submit the form.
    *   An area to display status messages (e.g., "Generating...", "Success!", or error messages).
    *   A download button that appears upon successful generation.

2.  **JavaScript Logic (`app.js`):**
    *   On page load, fetch the list of namespaces from `/api/namespaces` and populate the dropdown.
    *   Handle the form submission:
        *   Make a `POST` request to `/api/generate-kubeconfig` with the form data.
        *   On success, create a downloadable blob from the response and trigger a download for the user.
        *   Display appropriate status or error messages.

### Phase 3: Containerization & Deployment

1.  **Dockerfile:**
    *   Create a `Dockerfile` to package the Python backend and the static frontend files into a single container image. It will use a Python base image, install dependencies, and copy the application code.

2.  **OpenShift Deployment Files:**
    *   **`deployment.yaml`**: Defines the Deployment to run the application container in OpenShift.
    *   **`service.yaml`**: Exposes the application internally within the cluster.
    *   **`route.yaml`**: Exposes the application to the outside world.
    *   **`serviceaccount.yaml`**: Defines the ServiceAccount the application will use.
    *   **`clusterrole.yaml`**: Defines the `kubeconfig-generator` ClusterRole with the necessary permissions (excluding RBAC binding for now, as requested).
    *   **`clusterrolebinding.yaml`**: Binds the ClusterRole to the application's ServiceAccount.
