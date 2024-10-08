#!/bin/bash

aws_region="<YOUR_AWS_REGION>"
aws_access_key_id="<YOUR_AWS_ACCESS"
aws_secret_access_key="<YOUR_AWS_SECRET>"
ngrok_domain="<YOUR_NGROK_DOMAIN>"
ngrok_token="<YOUR_NGROK_TOKEN>"

declare -A secrets
secrets=(
    ["aws-region"]="data=$aws_region:ticketing"
    ["aws-access-key-id"]="data=$aws_access_key_id:ticketing"
    ["aws-secret-access-key"]="data=$aws_secret_access_key:ticketing"
    ["ngrok-domain"]="data=$ngrok_domain:ticketing"
    ["ngrok-token"]="data=$ngrok_token:ticketing"
)

# Create the namespace
kubectl get namespace ticketing >/dev/null 2>&1 || kubectl create namespace ticketing

# Delete the secrets if they exist
for secret in "${!secrets[@]}"; do
    if kubectl get secret "$secret" -n ticketing >/dev/null 2>&1; then
        echo "Secret $secret exists, deleting it..."
        kubectl delete secret "$secret" -n ticketing
    fi
done

# Create the secrets
for secret in "${!secrets[@]}"; do
    secret_details=${secrets[$secret]}
    secret_data=$(echo $secret_details | cut -d: -f1) # Segment before the colon
    namespace=$(echo $secret_details | cut -d: -f2) # Segment after the colon
    IFS='=' read -r key value <<< "$secret_data" # Split the secret data by the equals sign
    echo "Creating secret $secret in namespace $namespace with $key=$value"
    kubectl create secret generic "$secret" --from-literal="$key=$value" -n "$namespace"
done

# Delete the deployment if it exists
echo "Deleting deployment.yaml..."
kubectl delete -f deployment.yaml

# Wait for all pods to be terminated
echo "Waiting for all pods to be terminated..."
while kubectl get pods -n ticketing | grep -v "NAME" | grep -q "."; do
    sleep 2
done

# Apply the deployment.yaml file
echo "Applying deployment.yaml..."
kubectl apply -f deployment.yaml
