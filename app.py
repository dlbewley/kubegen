import os
from flask import Flask, jsonify, request, send_from_directory
from kubernetes import client, config
import yaml

app = Flask(__name__, static_folder='frontend', static_url_path='')

def get_k8s_api():
    config.load_incluster_config()
    return client.CoreV1Api()

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/namespaces')
def get_namespaces():
    try:
        api = get_k8s_api()
        print("Attempting to list namespaces...")
        namespaces_response = api.list_namespace()
        print(f"Found {len(namespaces_response.items)} namespaces")
        namespaces = [ns.metadata.name for ns in namespaces_response.items]
        print(f"Namespace names: {namespaces}")
        return jsonify(namespaces)
    except Exception as e:
        print(f"Error listing namespaces: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-kubeconfig', methods=['POST'])
def generate_kubeconfig():
    data = request.json
    namespace = data.get('namespace')
    sa_name = data.get('serviceAccountName')
    default_duration = int(os.environ.get('DEFAULT_TOKEN_DURATION', 3600))
    duration = data.get('tokenDuration', default_duration)

    if not all([namespace, sa_name]):
        return jsonify({"error": "namespace and serviceAccountName are required"}), 400

    try:
        api = get_k8s_api()
        
        # Create ServiceAccount if it doesn't exist
        try:
            api.read_namespaced_service_account(name=sa_name, namespace=namespace)
        except client.ApiException as e:
            if e.status == 404:
                sa_body = client.V1ServiceAccount(metadata=client.V1ObjectMeta(name=sa_name))
                api.create_namespaced_service_account(namespace=namespace, body=sa_body)
            else:
                raise

        # Generate Token using standard Kubernetes API
        token_request = {
            "apiVersion": "authentication.k8s.io/v1",
            "kind": "TokenRequest",
            "spec": {
                "expirationSeconds": int(duration)
            }
        }
        
        # Use the Kubernetes API to create the token
        token_response = api.create_namespaced_service_account_token(
            name=sa_name,
            namespace=namespace,
            body=token_request
        )
        token = token_response.status.token

        # Get external cluster URL (must be reachable from outside the cluster)
        external_cluster_url = os.environ.get('EXTERNAL_CLUSTER_URL')
        if not external_cluster_url:
            # Fallback to internal URL if external URL not configured
            cluster_url = os.environ.get('KUBERNETES_PORT_443_TCP_ADDR')
            if not cluster_url:
                cluster_url = f"https://{os.environ['KUBERNETES_SERVICE_HOST']}:{os.environ['KUBERNETES_SERVICE_PORT']}"
        else:
            # Use external URL but remove the protocol if present
            cluster_url = external_cluster_url.replace('https://', '').replace('http://', '')
        
        with open('/var/run/secrets/kubernetes.io/serviceaccount/ca.crt', 'r') as f:
            ca_data = f.read()

        # Encode ca_data to base64
        import base64
        ca_data = base64.b64encode(ca_data.encode('utf-8')).decode('utf-8')

        # Get Cluster Name
        cluster_name = os.environ.get('CLUSTER_NAME', 'openshift')

        # Construct Kubeconfig
        kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [{
                "name": cluster_name,
                "cluster": {
                    "server": f"https://{cluster_url}",
                    "certificate-authority-data": ca_data
                }
            }],
            "users": [{
                "name": sa_name,
                "user": { "token": token }
            }],
            "contexts": [{
                "name": f"{sa_name}@{cluster_name}",
                "context": {
                    "cluster": cluster_name,
                    "user": sa_name,
                    "namespace": namespace
                }
            }],
            "current-context": f"{sa_name}@{cluster_name}"
        }

        return jsonify(kubeconfig)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
