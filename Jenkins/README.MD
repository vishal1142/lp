Option 1: Shell Script Using Jenkins CLI (Recommended)

#!/bin/bash

# Define Jenkins URL and CLI path
JENKINS_URL="http://localhost:8080"
CLI_JAR="jenkins-cli.jar"
ADMIN_PASSWORD=$(docker exec <your-container-name> cat /var/jenkins_home/secrets/initialAdminPassword)

# Download Jenkins CLI
curl -o $CLI_JAR "$JENKINS_URL/jnlpJars/jenkins-cli.jar"

# Plugin list
PLUGINS=(
  workflow-aggregator
  pipeline-stage-view
  git
  matrix-auth
  docker-workflow
  credentials-binding
  blueocean
)

# Install plugins
for plugin in "${PLUGINS[@]}"
do
  echo "Installing plugin: $plugin"
  java -jar $CLI_JAR -s $JENKINS_URL -auth admin:$ADMIN_PASSWORD install-plugin $plugin
done

# Restart Jenkins to apply changes
java -jar $CLI_JAR -s $JENKINS_URL -auth admin:$ADMIN_PASSWORD safe-restart
