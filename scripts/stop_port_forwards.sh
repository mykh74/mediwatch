#!/bin/bash

# Stop all MediWatch port forwards

echo "🛑 Stopping all MediWatch port forwards..."

# Kill all kubectl port-forward processes for mediwatch namespace
pkill -f "kubectl port-forward.*mediwatch" 2>/dev/null

# Clean up PID files
rm -f /tmp/port-forward-*.pid 2>/dev/null

echo "✅ All port forwards stopped"

# Show any remaining port forwards
if pgrep -f "kubectl port-forward" > /dev/null; then
    echo ""
    echo "⚠️  Other port forwards still running:"
    pgrep -af "kubectl port-forward"
else
    echo "✅ No port forwards running"
fi
