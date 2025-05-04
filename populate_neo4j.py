#!/usr/bin/env python3
import os
import sys
import requests
import html
from bs4 import BeautifulSoup
from neo4j import GraphDatabase
from pathlib import Path

# Get the absolute path to the webapp directory
current_dir = Path(__file__).resolve().parent
webapp_dir = current_dir / "webapp"

# Add webapp to system path
sys.path.append(str(webapp_dir))

# Neo4j database credentials from environment variables
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
# Extract username and password from NEO4J_AUTH (format: username/password)
neo4j_auth = os.environ.get("NEO4J_AUTH", "neo4j/neo4j").split("/")
NEO4J_USER = neo4j_auth[0]
NEO4J_PASSWORD = neo4j_auth[1] if len(neo4j_auth) > 1 else "neo4j"

# Confluence API credentials from environment variables
CONFLUENCE_BASE_URL = os.environ.get("CONFLUENCE_BASE_URL", "")
CONFLUENCE_ACCESS_TOKEN = os.environ.get("CONFLUENCE_ACCESS_TOKEN", "")
CONFLUENCE_REFRESH_TOKEN = os.environ.get("CONFLUENCE_REFRESH_TOKEN", "")
CONFLUENCE_CLIENT_ID = os.environ.get("CONFLUENCE_CLIENT_ID", "")
CONFLUENCE_CLIENT_SECRET = os.environ.get("CONFLUENCE_CLIENT_SECRET", "")
CONFLUENCE_SPACE = os.environ.get("RDCRN_CONFLUENCE_SPACE", "")

# OpenAI API key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

class ConfluenceClient:
    def __init__(self):
        self.base_url = CONFLUENCE_BASE_URL
        self.access_token = CONFLUENCE_ACCESS_TOKEN
        self.refresh_token = CONFLUENCE_REFRESH_TOKEN
        self.client_id = CONFLUENCE_CLIENT_ID
        self.client_secret = CONFLUENCE_CLIENT_SECRET
        
        if not all([self.base_url, self.access_token, self.client_id]):
            print("WARNING: Confluence API credentials not fully configured in environment variables")
        
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_spaces(self):
        """Get all available Confluence spaces"""
        if not self.base_url or not self.access_token:
            print("ERROR: Confluence API credentials not configured")
            return {"results": []}
            
        url = f"{self.base_url}/api/v2/spaces"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting Confluence spaces: {str(e)}")
            return {"results": []}
    
    def get_pages(self, space_id):
        """Get all pages in a specific Confluence space"""
        if not self.base_url or not self.access_token:
            print("ERROR: Confluence API credentials not configured")
            return {"results": []}
            
        url = f"{self.base_url}/api/v2/pages"
        params = {'spaceId': space_id}
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting Confluence pages: {str(e)}")
            return {"results": []}
    
    def get_page_content(self, page_id):
        """Get the content of a specific Confluence page"""
        if not self.base_url or not self.access_token:
            print("ERROR: Confluence API credentials not configured")
            return None
            
        try:
            # First get the page metadata using v2 API
            url = f"{self.base_url}/api/v2/pages/{page_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Then get the page content using v1 API
            content_url = f"{self.base_url}/rest/api/content/{page_id}"
            params = {'expand': 'body.storage,space,version'}
            content_response = requests.get(content_url, headers=self.headers, params=params)
            content_response.raise_for_status()
            
            # Combine the metadata with the content
            page_data = {
                **response.json(),
                'content': content_response.json()
            }
            
            return page_data
        except Exception as e:
            print(f"Error getting Confluence page content: {str(e)}")
            return None

# Function to get embeddings from OpenAI
def get_embedding(text):
    if not OPENAI_API_KEY:
        # If no API key, return a random embedding as fallback
        import random
        return [random.random() for _ in range(1536)]
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        
        # Extract the embedding from the response
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        # Return a random embedding as fallback
        import random
        return [random.random() for _ in range(1536)]

# Functions to interact with Neo4j
def create_indexes(session):
    # Create vector index for Confluence data
    session.run("""
    CREATE VECTOR INDEX confluence_embedding IF NOT EXISTS
    FOR (n:Confluence)
    ON (n.embedding)
    OPTIONS {indexConfig: {
        `vector.dimensions`: 1536,
        `vector.similarity_function`: 'cosine'
    }}
    """)
    
    # Create fulltext index for keyword search
    session.run("""
    CREATE FULLTEXT INDEX confluence_keyword IF NOT EXISTS
    FOR (n:Confluence)
    ON EACH [n.id, n.text, n.title]
    """)
    
    print("Created Neo4j indexes")

def clear_existing_data(session):
    session.run("MATCH (n:Confluence) DETACH DELETE n")
    print("Cleared existing Confluence data")

def create_confluence_node(session, page):
    """Create a Neo4j node from a Confluence page"""
    try:
        # Extract relevant data from the page
        page_id = page.get('id')
        title = page.get('title', '')
        
        # Extract plain text content from HTML
        text = ""
        if 'content' in page and 'body' in page['content'] and 'storage' in page['content']['body']:
            html_content = page['content']['body']['storage']['value']
            
            # Use BeautifulSoup for better HTML parsing
            soup = BeautifulSoup(html_content, 'html.parser')
            # Get text and decode HTML entities
            text = html.unescape(soup.get_text(separator=' ', strip=True))
        
        # Generate embedding for the document text
        text_for_embedding = f"{title} {text}"
        embedding = get_embedding(text_for_embedding)
        
        # Create node in Neo4j
        session.run("""
        CREATE (n:Confluence {
            id: $id,
            title: $title,
            text: $text,
            embedding: $embedding
        })
        """, id=page_id, title=title, text=text, embedding=embedding)
        
        print(f"Created node for page: {title}")
        return True
    except Exception as e:
        print(f"Error creating node for page {page.get('title', 'Unknown')}: {str(e)}")
        return False

def fetch_and_store_confluence_data():
    """Fetch data from Confluence API and store in Neo4j"""
    client = ConfluenceClient()
    
    # Get spaces
    spaces = client.get_spaces()
    print(f"Found {len(spaces.get('results', []))} Confluence spaces")
    
    # Find the target space
    target_space = None
    for space in spaces.get('results', []):
        if space.get('key') == CONFLUENCE_SPACE:
            target_space = space
            break
    
    if not target_space:
        print(f"Warning: Could not find Confluence space with key {CONFLUENCE_SPACE}")
        # Try to use the first space if available
        if spaces.get('results', []):
            target_space = spaces['results'][0]
            print(f"Using first available space: {target_space.get('name')}")
        else:
            print("Error: No Confluence spaces found")
            return False
    
    # Get pages in the space
    pages_data = client.get_pages(target_space.get('id'))
    pages = pages_data.get('results', [])
    print(f"Found {len(pages)} pages in Confluence space {target_space.get('name')}")
    
    if not pages:
        print("No pages found in Confluence")
        return False
    
    # Initialize Neo4j session
    with driver.session() as session:
        # Clear existing data and create indexes
        clear_existing_data(session)
        create_indexes(session)
        
        # Process each page
        successful_pages = 0
        for page in pages:
            # Get full page content
            page_data = client.get_page_content(page.get('id'))
            if page_data:
                if create_confluence_node(session, page_data):
                    successful_pages += 1
        
        # Verify data was added
        result = session.run("MATCH (n:Confluence) RETURN count(n) as count")
        count = result.single()["count"]
        print(f"Successfully added {count} Confluence pages to Neo4j")
        
        return count > 0

def main():
    # Validate required environment variables
    missing_vars = []
    for var_name, var_value in [
        ("NEO4J_URI", NEO4J_URI),
        ("CONFLUENCE_BASE_URL", CONFLUENCE_BASE_URL),
        ("CONFLUENCE_ACCESS_TOKEN", CONFLUENCE_ACCESS_TOKEN),
        ("OPENAI_API_KEY", OPENAI_API_KEY)
    ]:
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"WARNING: The following environment variables are not set: {', '.join(missing_vars)}")
        print("The script may not function correctly without these variables.")
    
    if not OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY environment variable is not set. Using random embeddings as fallback.")
    
    print(f"Connecting to Neo4j at {NEO4J_URI} with user {NEO4J_USER}")
    
    # Fetch and store Confluence data
    success = fetch_and_store_confluence_data()
    
    if success:
        print("Successfully populated Neo4j with Confluence data")
    else:
        print("Failed to populate Neo4j with Confluence data")

if __name__ == "__main__":
    main()
    driver.close() 