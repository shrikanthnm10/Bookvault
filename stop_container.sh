#!/bin/bash

echo "=== Stopping BookVault App Container ==="

# Stop and remove existing container if running
if [ "$(docker ps -q -f name=bookvault-app)" ]; then
  echo "Stopping running bookvault-app container..."
  docker stop bookvault-app
  docker rm bookvault-app
  echo "Container stopped and removed."
else
  echo "No running bookvault-app container found. Skipping."
fi

# Clean up unused images to free disk space
echo "Pruning unused Docker images..."
docker image prune -f

echo "=== Cleanup complete ==="
