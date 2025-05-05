#!/bin/bash

# This script rebuilds the Neo4j database with the latest Confluence content
# using the improved HTML entity handling

echo "Rebuilding Neo4j database with improved HTML handling..."

# Source environment variables from load_data.sh
source load_data.sh

# Run the populate_neo4j.py script
python3 populate_neo4j.py

echo "Database rebuild complete" 