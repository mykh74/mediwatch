#!/bin/bash
# MediWatch Kubernetes Deployment Script
# This script deploys the complete MediWatch stack to Kubernetes

set -e

NAMESPACE="mediwatch"
IMAGE_TAG="${1:-latest}"

echo "=================================================="
echo "MediWatch Kubernetes Deployment"
echo "=================================================="
echo "Namespace: $NAMESPACE"
echo "Image Tag: $IMAGE_TAG"
echo "=================================================="

# Function to check if namespace exists
namespace_exists() {
    kubectl get namespace "$NAMESPACE" &> /dev/null
}

# Function to wait for deployment
wait_for_deployment() {
    local deployment=$1
    echo "⏳ Waiting for $deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s \
        deployment/$deployment -n $NAMESPACE || {
        echo "❌ $deployment failed to become ready"
        kubectl logs -n $NAMESPACE deployment/$deployment --tail=50
        return 1
    }
    echo "✅ $deployment is ready"
}

# 1. Create namespace if it doesn't exist
if ! namespace_exists; then
    echo "📦 Creating namespace $NAMESPACE..."
    kubectl apply -f ci-cd/kubernetes/namespace.yaml
else
    echo "✓ Namespace $NAMESPACE already exists"
fi

# 2. Apply ConfigMaps
echo "⚙️  Applying ConfigMaps..."
kubectl apply -f ci-cd/kubernetes/configmap.yaml

# 3. Create storage (PVCs)
echo "💾 Creating persistent volume claims..."
kubectl apply -f ci-cd/kubernetes/storage/pvc.yaml

# 4. Deploy MLflow (if not already deployed)
if ! kubectl get deployment mlflow -n $NAMESPACE &> /dev/null; then
    echo "📊 Deploying MLflow..."
    kubectl apply -f ci-cd/kubernetes/mlflow/deployment.yaml
    wait_for_deployment mlflow
else
    echo "✓ MLflow already deployed"
fi

# 5. Update API deployment with new image
echo "🔌 Updating API deployment..."
# Replace placeholder image in deployment manifest
sed "s|PLACEHOLDER_IMAGE|localhost/mediwatch-api:$IMAGE_TAG|g" \
    ci-cd/kubernetes/api/deployment.yaml | kubectl apply -f -

# 6. Apply Service and HPA
echo "🌐 Applying Service and HPA..."
kubectl apply -f ci-cd/kubernetes/api/service.yaml
kubectl apply -f ci-cd/kubernetes/api/hpa.yaml

# 7. Wait for API deployment
wait_for_deployment mediwatch-api

# 8. Get service information
echo ""
echo "=================================================="
echo "✅ Deployment Complete!"
echo "=================================================="
echo ""

# Get service endpoint
SERVICE_TYPE=$(kubectl get svc mediwatch-api-service -n $NAMESPACE -o jsonpath='{.spec.type}')
if [ "$SERVICE_TYPE" = "LoadBalancer" ]; then
    EXTERNAL_IP=$(kubectl get svc mediwatch-api-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(kubectl get svc mediwatch-api-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    if [ -n "$EXTERNAL_IP" ]; then
        echo "🌐 API URL: http://$EXTERNAL_IP"
    else
        echo "⏳ LoadBalancer IP pending... Check with: kubectl get svc -n $NAMESPACE"
    fi
else
    NODE_PORT=$(kubectl get svc mediwatch-api-service -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}')
    echo "🌐 API accessible via NodePort: $NODE_PORT"
fi

echo ""
echo "📊 MLflow: kubectl port-forward -n $NAMESPACE svc/mlflow-service 5000:5000"
echo ""
echo "🔍 View pods: kubectl get pods -n $NAMESPACE"
echo "📝 View logs: kubectl logs -f deployment/mediwatch-api -n $NAMESPACE"
echo "📈 View HPA: kubectl get hpa -n $NAMESPACE"
echo ""
echo "=================================================="
