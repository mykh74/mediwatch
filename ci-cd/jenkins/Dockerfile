FROM jenkins/jenkins:lts

USER root

# Install prerequisites
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Install Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli
    
# Set Docker CLI API version compatibility
ENV DOCKER_API_VERSION=1.43

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/kubectl && \
    kubectl version --client

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Give Jenkins user permissions for Docker socket
# This works by adding jenkins user to docker group and giving permissions
RUN usermod -aG docker jenkins || true
RUN groupmod -g 999 docker || true

# Fix permissions for docker socket (will be handled by entrypoint)
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch back to Jenkins user
USER jenkins

# Install Jenkins plugins (optional - pre-install common plugins)
RUN jenkins-plugin-cli --plugins \
    git \
    workflow-aggregator \
    docker-workflow \
    kubernetes \
    kubernetes-cli

# Switch back to root for entrypoint
USER root

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
