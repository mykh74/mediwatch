#!/bin/bash

# MediWatch Port Forward Setup Script
# This script sets up persistent port forwards for all services that need external access

set -e

echo "=============================================="
echo "🚀 MediWatch Port Forward Setup"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Kubernetes is accessible
echo -e "\n${YELLOW}📡 Checking Kubernetes connection...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    echo "Please ensure Docker Desktop with Kubernetes is running"
    exit 1
fi
echo -e "${GREEN}✅ Kubernetes cluster accessible${NC}"

# Check if mediwatch namespace exists
echo -e "\n${YELLOW}🔍 Checking mediwatch namespace...${NC}"
if ! kubectl get namespace mediwatch &> /dev/null; then
    echo -e "${RED}❌ Namespace 'mediwatch' not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Namespace 'mediwatch' exists${NC}"

# Kill any existing port forwards
echo -e "\n${YELLOW}🧹 Cleaning up existing port forwards...${NC}"
pkill -f "kubectl port-forward.*mediwatch" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅ Cleaned up old port forwards${NC}"

# Function to start a port forward
start_port_forward() {
    local service=$1
    local local_port=$2
    local remote_port=$3
    local name=$4
    
    echo -e "\n${YELLOW}🔌 Setting up port forward for $name...${NC}"
    
    # Check if service exists
    if ! kubectl get svc "$service" -n mediwatch &> /dev/null; then
        echo -e "${RED}❌ Service $service not found${NC}"
        return 1
    fi
    
    # Check if pod is ready (simplified check)
    local pod_count=$(kubectl get pods -n mediwatch --field-selector=status.phase=Running 2>/dev/null | wc -l)
    if [ "$pod_count" -lt 2 ]; then
        echo -e "${RED}❌ No running pods found in mediwatch namespace${NC}"
        return 1
    fi
    
    # Start port forward in background
    nohup kubectl port-forward -n mediwatch "svc/$service" "$local_port:$remote_port" > "/tmp/port-forward-$name.log" 2>&1 &
    local pid=$!
    
    # Wait a moment and check if it's still running
    sleep 2
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}✅ $name: http://localhost:$local_port (PID: $pid)${NC}"
        echo "$pid" > "/tmp/port-forward-$name.pid"
        return 0
    else
        echo -e "${RED}❌ Failed to start port forward for $name${NC}"
        cat "/tmp/port-forward-$name.log"
        return 1
    fi
}

# Set up port forwards
echo -e "\n${YELLOW}🌐 Setting up service port forwards...${NC}"

# MLflow (internal service, needs port forward)
start_port_forward "mlflow-service" 5000 5000 "mlflow"

# Evidently (internal service, needs port forward)
start_port_forward "evidently-service" 8800 8000 "evidently"

# Optional: Add more services as needed
# start_port_forward "service-name" local_port remote_port "display-name"

echo -e "\n=============================================="
echo -e "${GREEN}✅ Port Forward Setup Complete!${NC}"
echo "=============================================="

echo -e "\n📊 Service Access URLs:"
echo -e "${GREEN}• MediWatch API:${NC}      http://localhost (already exposed via LoadBalancer)"
echo -e "${GREEN}• API Docs:${NC}           http://localhost/docs"
echo -e "${GREEN}• Airflow:${NC}            http://localhost:8080 (already exposed via LoadBalancer)"
echo -e "${GREEN}• MLflow:${NC}             http://localhost:5000 (port-forward)"
echo -e "${GREEN}• Evidently:${NC}          http://localhost:8800 (port-forward)"
echo -e "${GREEN}• Jenkins:${NC}            http://localhost:8081 (running in Docker)"

echo -e "\n📝 Port Forward Logs:"
echo "• MLflow:    /tmp/port-forward-mlflow.log"
echo "• Evidently: /tmp/port-forward-evidently.log"

echo -e "\n🛑 To stop all port forwards:"
echo "   pkill -f 'kubectl port-forward.*mediwatch'"
echo "   # Or run: ./scripts/stop_port_forwards.sh"

echo -e "\n💡 Tip: Port forwards will stop if this terminal is closed."
echo "   To keep them running, use screen or tmux."

echo -e "\n${GREEN}Press Ctrl+C to stop monitoring (port forwards will continue in background)${NC}"
echo "Or press Enter to continue..."
read -t 5 || true

echo -e "\n${GREEN}✅ Setup complete! Services are accessible at the URLs above.${NC}"
