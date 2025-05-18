#!/bin/bash

# Check if .env file already exists
if [ -f .env ]; then
  echo ".env file already exists, skipping creation."
  exit 0
fi

# Extract values from load_data.sh
CONFLUENCE_ACCESS_TOKEN=$(grep "CONFLUENCE_ACCESS_TOKEN" load_data.sh | grep -oP 'export CONFLUENCE_ACCESS_TOKEN="\K[^"]+')
CONFLUENCE_REFRESH_TOKEN=$(grep "CONFLUENCE_REFRESH_TOKEN" load_data.sh | grep -oP 'export CONFLUENCE_REFRESH_TOKEN="\K[^"]+')
CONFLUENCE_BASE_URL=$(grep "CONFLUENCE_BASE_URL" load_data.sh | grep -oP 'export CONFLUENCE_BASE_URL="\K[^"]+')
CONFLUENCE_CLIENT_ID=$(grep "CONFLUENCE_CLIENT_ID" load_data.sh | grep -oP 'export CONFLUENCE_CLIENT_ID="\K[^"]+')
CONFLUENCE_CLIENT_SECRET=$(grep "CONFLUENCE_CLIENT_SECRET" load_data.sh | grep -oP 'export CONFLUENCE_CLIENT_SECRET="\K[^"]+')
OPENAI_API_KEY=$(grep "OPENAI_API_KEY" load_data.sh | grep -oP 'export OPENAI_API_KEY="\K[^"]+')
RDCRN_CONFLUENCE_SPACE=$(grep "RDCRN_CONFLUENCE_SPACE" load_data.sh | grep -oP 'export RDCRN_CONFLUENCE_SPACE="\K[^"]+')

# Create .env file
cat > .env << EOL
# API Keys and Authentication
CONFLUENCE_ACCESS_TOKEN=${CONFLUENCE_ACCESS_TOKEN}
CONFLUENCE_REFRESH_TOKEN=${CONFLUENCE_REFRESH_TOKEN}
CONFLUENCE_BASE_URL=${CONFLUENCE_BASE_URL}
CONFLUENCE_CLIENT_ID=${CONFLUENCE_CLIENT_ID}
CONFLUENCE_CLIENT_SECRET=${CONFLUENCE_CLIENT_SECRET}
OPENAI_API_KEY=${OPENAI_API_KEY}
RDCRN_CONFLUENCE_SPACE=${RDCRN_CONFLUENCE_SPACE}

# Neo4j Configuration
NEO4J_AUTH=neo4j/root@neo4j
NEO4J_URI=bolt://neo4j:7687

# Data Loading Flag (set to 'true' to load data on startup)
LOAD_DATA=true
EOL

echo ".env file created successfully." 