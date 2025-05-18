#!/bin/bash

# This script rebuilds the Neo4j database with the latest Confluence content

echo "Rebuilding Neo4j database..."

# Execute the load_data.sh script which will handle Docker operations
./load_data.sh

echo "Database rebuild complete" 