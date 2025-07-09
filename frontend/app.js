document.addEventListener('DOMContentLoaded', () => {
    const namespaceSelect = document.getElementById('namespace');
    const form = document.getElementById('kubeconfig-form');
    const statusDiv = document.getElementById('status');
    const downloadBtn = document.getElementById('download-btn');
    let kubeconfigContent = null;

    // Fetch namespaces on page load
    fetch('/api/namespaces')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            data.forEach(ns => {
                const option = document.createElement('option');
                option.value = ns;
                option.textContent = ns;
                namespaceSelect.appendChild(option);
            });
        })
        .catch(error => {
            statusDiv.textContent = `Error fetching namespaces: ${error.message}`;
            statusDiv.style.color = 'red';
        });

    // Handle form submission
    form.addEventListener('submit', (event) => {
        event.preventDefault();
        statusDiv.textContent = 'Generating...';
        statusDiv.style.color = 'black';
        downloadBtn.style.display = 'none';

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        fetch('/api/generate-kubeconfig', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            statusDiv.textContent = 'Kubeconfig generated successfully!';
            statusDiv.style.color = 'green';
            const yaml = jsyaml.dump(data);
            kubeconfigContent = yaml;
            downloadBtn.style.display = 'block';
        })
        .catch(error => {
            statusDiv.textContent = `Error: ${error.message}`;
            statusDiv.style.color = 'red';
        });
    });

    // Handle download button click
    downloadBtn.addEventListener('click', () => {
        if (kubeconfigContent) {
            const blob = new Blob([kubeconfigContent], { type: 'application/yaml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'kubeconfig.yaml';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    });
});
