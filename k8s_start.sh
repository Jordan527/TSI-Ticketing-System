#!/bin/bash

set -e

aws_region="<aws_region>"
aws_access_key_id="<aws_access_key_id>"
aws_secret_access_key="<aws_secret_access_key>"
ngrok_domain="<ngrok_domain>"
ngrok_token="<ngrok_token>"
ngrok_api_key="<ngrok_api_key>"

# <repo_name>:<repo_chart>:<repo_url>:<repo_namespace>
declare -A helm_repos
helm_repos=(
    ["ngrok-ingress-controller"]="ngrok:ngrok/kubernetes-ingress-controller:https://charts.ngrok.com:ticketing"
)

declare -A secrets
secrets=(
    ["aws-region"]="data=$aws_region:ticketing"
    ["aws-access-key-id"]="data=$aws_access_key_id:ticketing"
    ["aws-secret-access-key"]="data=$aws_secret_access_key:ticketing"
)

create_namespaces() {
    # Create the namespace
    kubectl get namespace ticketing >/dev/null 2>&1 || kubectl create namespace ticketing
}

check_and_add_helm_repos() {
    for repo in "${!helm_repos[@]}"; do
        repo_details=${helm_repos[$repo]}
        repo_name=$(echo $repo_details | cut -d: -f1)       # Segment before the colon
        repo_url_prefix=$(echo $repo_details | cut -d: -f3) # Segment after the second colon
        repo_url_domain=$(echo $repo_details | cut -d: -f4) # Segment after the third colon
        repo_url="$repo_url_prefix:$repo_url_domain"
        echo "Adding repo $repo_name with URL $repo_url..."
        if helm repo list | grep -q "$repo_name"; then
            echo "Repo $repo_name exists, updating it..."
            helm repo update "$repo_name"
        else
            echo "Adding repo $repo_name with URL $repo_url..."
            helm repo add "$repo_name" "$repo_url"
        fi
    done
}

install_helm_charts() {
    for repo in "${!helm_repos[@]}"; do
        repo_details=${helm_repos[$repo]}
        repo_name=$(echo $repo_details | cut -d: -f1)      # Segment before the colon
        repo_chart=$(echo $repo_details | cut -d: -f2)     # Segment after the first colon
        repo_namespace=$(echo $repo_details | cut -d: -f5) # Segment after the third colon
        if helm list -n "$repo_namespace" | grep -q "$repo"; then
            echo "Chart $repo_chart already exists in namespace $repo_namespace..."
        else
            echo "Installing chart $repo_chart in namespace $repo_namespace..."
            helm install "$repo" "$repo_chart" \
                --namespace "$repo_namespace" \
                --create-namespace \
                --set credentials.apiKey=$ngrok_api_key \
                --set credentials.authtoken=$ngrok_token
        fi
    done
}

create_secrets() {
    # Delete the secrets if they exist
    for secret in "${!secrets[@]}"; do
        secret_details=${secrets[$secret]}
        namespace=$(echo $secret_details | cut -d: -f2) # Segment after the colon
        if kubectl get secret "$secret" -n "$namespace" >/dev/null 2>&1; then
            echo "Secret $secret exists, deleting it..."
            kubectl delete secret "$secret" -n "$namespace"
        fi
    done

    # Create the secrets
    for secret in "${!secrets[@]}"; do
        secret_details=${secrets[$secret]}
        secret_data=$(echo $secret_details | cut -d: -f1) # Segment before the colon
        namespace=$(echo $secret_details | cut -d: -f2)   # Segment after the colon
        IFS='=' read -r key value <<<"$secret_data"       # Split the secret data by the equals sign
        echo "Creating secret $secret in namespace $namespace with $key=$value"
        kubectl create secret generic "$secret" --from-literal="$key=$value" -n "$namespace"
    done
}

# Create the ngrok.yaml file so that the domain is set from the variable
create_ngrok_yaml() {
    cat <<EOF >ngrok.yaml
apiVersion: v1
kind: Service
metadata:
  name: ticketing-proxy
  namespace: ticketing
spec:
  ports:
    - name: http
      port: 80
      targetPort: 5000
  selector:
    app: flask-app
---
# ngrok Ingress Controller Configuration
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ticketing-proxy-ingress
  namespace: ticketing
spec:
  ingressClassName: ngrok
  rules:
    - host: "${ngrok_domain}"
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ticketing-proxy
                port:
                  number: 80
EOF
}

deploy_ngrok() {
    # Apply the ngrok.yaml file
    echo "Applying ngrok.yaml..."
    kubectl apply -f ngrok.yaml
}

deploy_flask() {
    # Apply the flask.yaml file
    echo "Applying flask.yaml..."
    kubectl apply -f flask.yaml
}

initialise_flask() {
    # Wait for a flask pod to be running
    echo "Waiting for a flask pod to be running..."
    kubectl wait --for=condition=Ready pod -l app=flask-app -n ticketing --timeout=20s

    # Initialise the flask app
    echo "Initialising the flask app..."
    curl -X POST http://"$ngrok_domain"/initialise
    echo "Flask app initialised!"
}

main() {
    create_ngrok_yaml
    create_namespaces
    check_and_add_helm_repos
    install_helm_charts
    create_secrets
    deploy_ngrok
    deploy_flask
    initialise_flask
}

main