# DocuQueryAI

DocuQueryAI is an intelligent document search platform that leverages Neo4j graph database and AI to provide semantic search across Confluence spaces and other data sources. It extracts, indexes, and makes your documentation easily searchable through a modern web interface with AI-powered responses.

## Features

- **AI-Powered Search**: Get direct, concise answers to your questions based on your documentation
- **Confluence Integration**: Automatically retrieve and index content from Confluence spaces
- **Graph Database**: Use Neo4j for efficient storage and retrieval of document relationships
- **Semantic Search**: Find relevant information even when queries don't match exact keywords
- **Modern UI**: Clean, responsive React frontend with markdown support
- **Source Attribution**: See exactly which documents were used to answer your questions
- **Docker Support**: Easy deployment with containerization for both development and production

## Architecture

The system consists of:

- **Frontend**: React application with ReactMarkdown for rendering responses
- **Backend**: Django API for handling search requests
- **Database**: Neo4j graph database for document storage and vector search
- **AI Integration**: LangChain with OpenAI for generating answers from relevant documents

## Prerequisites

- Docker and Docker Compose
- Confluence API credentials (for Confluence integration)
- OpenAI API key (for embeddings and response generation)

## Quick Start

1. Clone this repository:
```bash
git clone https://github.com/yourusername/doc-ai.git
cd doc-ai
```

2. Create a `.env` file with the following variables:
```
# Neo4j Configuration
NEO4J_AUTH=neo4j/yourpassword
NEO4J_URI=bolt://neo4j:7687

# Confluence API Configuration
CONFLUENCE_BASE_URL=https://your-instance.atlassian.net/wiki
CONFLUENCE_ACCESS_TOKEN=your_access_token
CONFLUENCE_REFRESH_TOKEN=your_refresh_token
CONFLUENCE_CLIENT_ID=your_client_id
CONFLUENCE_CLIENT_SECRET=your_client_secret

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key
```

3. Start the application:
```bash
docker-compose up -d
```

4. Load data from Confluence:
```bash
./load_data.sh
```

5. Access the application:
   - Frontend: http://localhost:3010
   - Backend API: http://localhost:8010/api/search/?q=your+query
   - Neo4j Browser: http://localhost:7490 (username: neo4j, password: from NEO4J_AUTH)

## Data Loading

The system loads data from Confluence into Neo4j using the `populate_neo4j.py` script. This script:

1. Fetches all available Confluence spaces
2. Retrieves pages from each space
3. Extracts content and metadata
4. Generates embeddings using OpenAI
5. Stores the data in Neo4j with appropriate indexes

To reload data manually:
```bash
./load_data.sh
```

## Search Process

When a user submits a query:

1. The frontend sends the query to the Django backend
2. The backend performs these steps:
   - Retrieves relevant documents from Neo4j using vector similarity search
   - Checks user permissions for the documents
   - Evaluates document relevance to the query
   - Generates an answer based on the relevant documents
3. The response is formatted with markdown and displayed in the frontend

## Production Deployment

For production deployment, use the production Docker Compose file:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

See `ec2_deployment_guide.md` for detailed instructions on deploying to AWS EC2.

## Customization

### Modifying the AI Prompt

To modify how the AI generates responses, edit the prompt template in `webapp/docuquery/graph/DocuQueryMultiRetriever.py`.

### Adding Data Sources

The system is designed to support multiple data sources. Currently, it includes:
- Confluence integration
- (Commented out) PostgreSQL integration

To add additional data sources, create a new retriever in the `docuquery/graph/neo4j_retrievers/` directory.

## Troubleshooting

- **Connection Issues**: Ensure all ports are correctly configured in Docker Compose files
- **No Documents Found**: Check Confluence API credentials and verify data loading
- **API Errors**: Check Django logs by running `docker-compose logs django`

## License

This project is released under the MIT License. 