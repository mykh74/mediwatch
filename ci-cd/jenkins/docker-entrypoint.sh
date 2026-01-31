#!/bin/bash
set -e

# Fix Docker socket permissions
if [ -S /var/run/docker.sock ]; then
    DOCKER_SOCK_GID=$(stat -c '%g' /var/run/docker.sock 2>/dev/null || stat -f '%g' /var/run/docker.sock)
    
    echo "Docker socket GID: $DOCKER_SOCK_GID"
    
    # Skip if GID is 0 (root)
    if [ "$DOCKER_SOCK_GID" != "0" ]; then
        # Create docker group if it doesn't exist with correct GID
        if ! getent group docker > /dev/null 2>&1; then
            groupadd -g $DOCKER_SOCK_GID docker
        else
            # Update docker group GID to match host if different
            CURRENT_GID=$(getent group docker | cut -d: -f3)
            if [ "$CURRENT_GID" != "$DOCKER_SOCK_GID" ]; then
                groupmod -g $DOCKER_SOCK_GID docker
            fi
        fi
        
        # Add jenkins user to docker group
        usermod -aG docker jenkins
    fi
    
    # Give permissions to socket
    chmod 666 /var/run/docker.sock || true
    
    echo "✓ Docker socket permissions configured"
fi

# Fix jenkins_home permissions
chown -R jenkins:jenkins /var/jenkins_home || true

# Start Jenkins with proper PID 1 handling
exec /usr/bin/tini -s -- /usr/local/bin/jenkins.sh
