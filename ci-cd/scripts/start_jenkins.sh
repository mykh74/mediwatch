#!/bin/bash
#
# Jenkins Quick Start Script
# Starts Jenkins with Docker Compose and provides initial setup information
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================="
echo "MediWatch Jenkins CI/CD Setup"
echo "========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Navigate to ci-cd directory
cd "$SCRIPT_DIR"

# Check if Jenkins is already running
if docker ps | grep -q jenkins; then
    echo "⚠️  Jenkins is already running!"
    echo ""
    echo "Options:"
    echo "  1. Stop and restart: docker-compose -f docker-compose.jenkins.yml restart"
    echo "  2. View logs: docker logs -f jenkins"
    echo "  3. Stop: docker-compose -f docker-compose.jenkins.yml down"
    echo ""
    exit 0
fi

# Start Jenkins
echo "Starting Jenkins..."
docker-compose -f docker-compose.jenkins.yml up -d

echo ""
echo "Waiting for Jenkins to start (this may take 1-2 minutes)..."
sleep 10

# Wait for Jenkins to be ready
MAX_WAIT=120
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if docker exec jenkins test -f /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null; then
        break
    fi
    echo -n "."
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

echo ""
echo ""

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "⚠️  Jenkins is taking longer than expected to start"
    echo "   Check logs: docker logs -f jenkins"
    exit 1
fi

echo "========================================="
echo "✓ Jenkins Started Successfully!"
echo "========================================="
echo ""
echo "📍 Access Jenkins at: http://localhost:8080"
echo ""

# Get initial admin password
if docker exec jenkins test -f /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null; then
    ADMIN_PASSWORD=$(docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "Unable to retrieve")
    echo "🔑 Initial Admin Password:"
    echo "   $ADMIN_PASSWORD"
    echo ""
    echo "   Copy this password to complete the setup wizard"
else
    echo "⚠️  Could not retrieve initial admin password"
    echo "   Get it with: docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword"
fi

echo ""
echo "========================================="
echo "Next Steps:"
echo "========================================="
echo ""
echo "1. Open http://localhost:8080 in your browser"
echo "2. Enter the initial admin password shown above"
echo "3. Click 'Install suggested plugins'"
echo "4. Create your admin user account"
echo "5. Complete the setup wizard"
echo ""
echo "Then:"
echo "6. Follow docs/JENKINS_SETUP.md for pipeline configuration"
echo "7. Create the 'mediwatch-ci-cd' pipeline job"
echo "8. Test the build!"
echo ""
echo "========================================="
echo "Useful Commands:"
echo "========================================="
echo ""
echo "View Jenkins logs:"
echo "  docker logs -f jenkins"
echo ""
echo "Stop Jenkins:"
echo "  docker-compose -f docker-compose.jenkins.yml down"
echo ""
echo "Restart Jenkins:"
echo "  docker-compose -f docker-compose.jenkins.yml restart"
echo ""
echo "Access Jenkins container:"
echo "  docker exec -it jenkins bash"
echo ""
echo "========================================="
