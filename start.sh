#!/bin/bash

# Stop any running containers
echo "Stopping any running containers..."
docker-compose down

# Build the containers
echo "Building containers..."
docker-compose build

# Start the containers in detached mode
echo "Starting containers..."
docker-compose up -d

# Display logs
echo "Displaying logs (press Ctrl+C to stop viewing logs)..."
docker-compose logs -f 