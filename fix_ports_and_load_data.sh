#!/bin/bash

# This script fixes port configurations and loads data for the DocAI application

echo "=============================================="
echo "Fixing port configurations and loading data..."
echo "=============================================="

# Stop any running containers
echo "Stopping any running containers..."
docker compose down

# Make sure the .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    ./load_data.sh
    # The load_data.sh script creates the .env file
else
    echo ".env file already exists."
fi

# Start the application
echo "Starting the application..."
docker compose up -d

# Wait for Neo4j to be ready
echo "Waiting for services to start..."
sleep 15

# Load the data
echo "Loading data into Neo4j..."
docker compose exec django python3 populate_neo4j.py

echo "=============================================="
echo "Setup complete! Your application is now running with the following ports:"
echo "Django API: http://localhost:8000"
echo "React Frontend: http://localhost:3000"
echo "Neo4j Browser: http://localhost:7474"
echo "Neo4j Bolt: localhost:7687"
echo "==============================================" 