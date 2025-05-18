#!/bin/bash

# Stop any running containers
echo "Stopping any running containers..."
docker-compose -f docker-compose.prod.yml down

# Build the containers
echo "Building containers..."
docker-compose -f docker-compose.prod.yml build

# Start the containers in detached mode
echo "Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Display logs
echo "Displaying logs (press Ctrl+C to stop viewing logs)..."
docker-compose -f docker-compose.prod.yml logs -f 