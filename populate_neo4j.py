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
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
# Extract username and password from NEO4J_AUTH (format: username/password)
neo4j_auth = os.environ.get("NEO4J_AUTH", "neo4j/root@neo4j").split("/")
NEO4J_USER = neo4j_auth[0]
NEO4J_PASSWORD = neo4j_auth[1] if len(neo4j_auth) > 1 else "password"

# Confluence API credentials from environment variables
CONFLUENCE_BASE_URL = os.environ.get("CONFLUENCE_BASE_URL", "")
CONFLUENCE_ACCESS_TOKEN = os.environ.get("CONFLUENCE_ACCESS_TOKEN", "")
CONFLUENCE_REFRESH_TOKEN = os.environ.get("CONFLUENCE_REFRESH_TOKEN", "")
CONFLUENCE_CLIENT_ID = os.environ.get("CONFLUENCE_CLIENT_ID", "")
CONFLUENCE_CLIENT_SECRET = os.environ.get("CONFLUENCE_CLIENT_SECRET", "")
# This is now used only as a fallback if no spaces are found
CONFLUENCE_SPACE = os.environ.get("RDCRN_CONFLUENCE_SPACE", "")
# Specific Confluence space to target (set to empty to load ALL spaces)
TARGET_SPACE_KEY = os.environ.get("TARGET_SPACE_KEY", "")

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
        
        missing_credentials = []
        if not self.base_url:
            missing_credentials.append("CONFLUENCE_BASE_URL")
        if not self.access_token:
            missing_credentials.append("CONFLUENCE_ACCESS_TOKEN")
        
        if missing_credentials:
            print(f"WARNING: The following required Confluence credentials are missing: {', '.join(missing_credentials)}")
        
        print(f"Initializing Confluence client with base URL: {self.base_url}")
        
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
        
        print(f"Fetching all Confluence spaces from {self.base_url}/api/v2/spaces")
            
        url = f"{self.base_url}/api/v2/spaces"
        params = {"limit": 100}  # Maximum allowed per request
        all_spaces = []
        
        try:
            # Implement pagination to get ALL spaces
            while url:
                print(f"Fetching spaces from {url}...")
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Add results to our collection
                all_spaces.extend(data.get('results', []))
                
                # Check if there are more spaces
                if 'next' in data.get('_links', {}):
                    # For next request, we follow the next link but need to fix the URL
                    next_link = data['_links']['next']
                    # Make sure we don't double the base URL
                    if next_link.startswith('/'):
                        url = self.base_url + next_link
                    else:
                        url = next_link
                    params = {}  # Next URL already includes parameters
                else:
                    # No more spaces
                    break
                    
            return {"results": all_spaces}
        except requests.exceptions.ConnectionError as e:
            print(f"ERROR: Connection error when accessing Confluence API: {str(e)}")
            print("Please check if the Confluence URL is correct and accessible from the container.")
            return {"results": []}
        except Exception as e:
            print(f"ERROR getting Confluence spaces: {str(e)}")
            return {"results": []}
    
    def get_pages(self, space_id):
        """Get all pages in a specific Confluence space"""
        if not self.base_url or not self.access_token:
            print("ERROR: Confluence API credentials not configured")
            return {"results": []}
            
        url = f"{self.base_url}/api/v2/pages"
        params = {'spaceId': space_id, 'limit': 100}  # Use maximum allowed per request
        all_pages = []
        
        try:
            # Implement pagination to get ALL pages
            page_count = 1
            while url:
                print(f"  Fetching pages page {page_count} from {url}...")
                # Fix any URL issues
                if "wiki/wiki" in url:
                    url = url.replace("wiki/wiki", "wiki")
                
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Add results to our collection
                new_results = data.get('results', [])
                print(f"  Found {len(new_results)} pages in this batch")
                all_pages.extend(new_results)
                
                # Check for 'next' URL in Link header which is more reliable
                if 'Link' in response.headers:
                    link_header = response.headers['Link']
                    if 'rel="next"' in link_header:
                        # Extract next URL from Link header
                        import re
                        next_match = re.search('<([^>]*)>; rel="next"', link_header)
                        if next_match:
                            next_url = next_match.group(1)
                            # Confluence sometimes returns relative URLs
                            if next_url.startswith('/'):
                                url = self.base_url + next_url.replace('/wiki/', '/')
                            else:
                                url = next_url
                            # No longer need the params
                            params = {}
                            page_count += 1
                            continue
                
                # Fallback to JSON _links if Link header not found
                if 'next' in data.get('_links', {}):
                    next_link = data['_links']['next']
                    # Handle relative URLs
                    if next_link.startswith('/'):
                        url = self.base_url + next_link.replace('/wiki/', '/')
                    else:
                        url = next_link
                    params = {}  # Next URL already includes parameters
                    page_count += 1
                else:
                    # No more pages
                    break
                    
            print(f"  Retrieved a total of {len(all_pages)} pages across {page_count} API calls")
            return {"results": all_pages}
        except Exception as e:
            print(f"Error getting Confluence pages: {str(e)}")
            print(f"URL that caused error: {url}")
            return {"results": []}
    
    def get_page_content(self, page_id):
        """Get the content of a specific Confluence page"""
        if not self.base_url or not self.access_token:
            print("ERROR: Confluence API credentials not configured")
            return None
            
        url = f"{self.base_url}/api/v2/pages/{page_id}"
        params = {'body-format': 'storage'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting Confluence page content: {str(e)}")
            return None

    def get_child_pages(self, parent_id):
        """Get all child pages of a specific Confluence page"""
        if not self.base_url or not self.access_token:
            print("ERROR: Confluence API credentials not configured")
            return {"results": []}
            
        url = f"{self.base_url}/api/v2/pages/{parent_id}/children"
        params = {'limit': 100}  # Use maximum allowed per request
        all_children = []
        
        try:
            # Implement pagination to get ALL child pages
            page_count = 1
            while url:
                print(f"    Fetching child pages page {page_count} from {url}...")
                # Fix any URL issues
                if "wiki/wiki" in url:
                    url = url.replace("wiki/wiki", "wiki")
                    
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Add results to our collection
                new_results = data.get('results', [])
                print(f"    Found {len(new_results)} child pages in this batch")
                all_children.extend(new_results)
                
                # Check for 'next' URL in Link header which is more reliable
                if 'Link' in response.headers:
                    link_header = response.headers['Link']
                    if 'rel="next"' in link_header:
                        # Extract next URL from Link header
                        import re
                        next_match = re.search('<([^>]*)>; rel="next"', link_header)
                        if next_match:
                            next_url = next_match.group(1)
                            # Confluence sometimes returns relative URLs
                            if next_url.startswith('/'):
                                url = self.base_url + next_url.replace('/wiki/', '/')
                            else:
                                url = next_url
                            # No longer need the params
                            params = {}
                            page_count += 1
                            continue
                
                # Fallback to JSON _links if Link header not found
                if 'next' in data.get('_links', {}):
                    next_link = data['_links']['next']
                    # Handle relative URLs
                    if next_link.startswith('/'):
                        url = self.base_url + next_link.replace('/wiki/', '/')
                    else:
                        url = next_link
                    params = {}  # Next URL already includes parameters
                    page_count += 1
                else:
                    # No more pages
                    break
                    
            if page_count > 1:
                print(f"    Retrieved a total of {len(all_children)} child pages across {page_count} API calls")
            return {"results": all_children}
        except Exception as e:
            print(f"Error getting Confluence child pages: {str(e)}")
            print(f"URL that caused error: {url}")
            return {"results": []}

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
    ON EACH [n.id, n.text, n.title, n.space_name, n.space_key]
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
        space_name = page.get('space_name', '')
        space_key = page.get('space_key', '')
        
        # Extract plain text content from HTML
        text = ""
        
        # Check if body content is in the v2 API format
        if 'body' in page and 'storage' in page.get('body', {}):
            html_content = page['body']['storage'].get('value', '')
            soup = BeautifulSoup(html_content, 'html.parser')
            text = html.unescape(soup.get_text(separator=' ', strip=True))
        # Check for the v1 API format
        elif 'content' in page and 'body' in page.get('content', {}) and 'storage' in page.get('content', {}).get('body', {}):
            html_content = page['content']['body']['storage'].get('value', '')
            soup = BeautifulSoup(html_content, 'html.parser')
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
            space_name: $space_name,
            space_key: $space_key,
            embedding: $embedding
        })
        """, id=page_id, title=title, text=text, space_name=space_name, space_key=space_key, embedding=embedding)
        
        print(f"  Created node for page: {title} (Space: {space_name})")
        return True
    except Exception as e:
        print(f"  Error creating node for page {page.get('title', 'Unknown')}: {str(e)}")
        return False

def fetch_and_store_confluence_data():
    """Fetch data from Confluence API and store in Neo4j"""
    client = ConfluenceClient()
    
    # Get spaces
    spaces = client.get_spaces()
    print(f"Found {len(spaces.get('results', []))} Confluence spaces")
    
    # Filter for target space if specified
    if TARGET_SPACE_KEY:
        print(f"Filtering for target space key: {TARGET_SPACE_KEY}")
        filtered_spaces = [space for space in spaces.get('results', []) if space.get('key') == TARGET_SPACE_KEY]
        if filtered_spaces:
            spaces['results'] = filtered_spaces
            print(f"Found target space: {filtered_spaces[0].get('name')} (ID: {filtered_spaces[0].get('id')})")
        else:
            print(f"WARNING: Target space '{TARGET_SPACE_KEY}' not found among available spaces")
    else:
        print("Loading ALL available Confluence spaces")
    
    if not spaces.get('results', []):
        print("Error: No Confluence spaces found")
        return False
        
    # Print available spaces
    print("\nAvailable spaces:")
    for i, space in enumerate(spaces.get('results', []), 1):
        print(f"  {i}. {space.get('name')} (Key: {space.get('key')}, ID: {space.get('id')})")
    print("")
        
    # Initialize Neo4j session
    with driver.session() as session:
        # Clear existing data and create indexes
        clear_existing_data(session)
        create_indexes(session)
        
        total_spaces = len(spaces.get('results', []))
        successful_pages = 0
        total_pages = 0
        processed_page_ids = set()  # Keep track of processed pages to avoid duplicates
        
        # Process all spaces
        for space_index, space in enumerate(spaces.get('results', []), 1):
            try:
                print(f"\nProcessing space {space_index}/{total_spaces}: {space.get('name')} (ID: {space.get('id')})")
                
                # Get pages in the space
                pages_data = client.get_pages(space.get('id'))
                pages = pages_data.get('results', [])
                print(f"  Found {len(pages)} top-level pages in Confluence space {space.get('name')}")
                
                if not pages:
                    print(f"  WARNING: No pages found in space {space.get('name')} (Key: {space.get('key')})")
                    continue
                
                # Create a queue to process all pages including children
                pages_to_process = list(pages)  # Start with top-level pages
                
                # Process all pages in the queue
                page_index = 0
                while page_index < len(pages_to_process):
                    page = pages_to_process[page_index]
                    page_index += 1
                    
                    if page.get('id') in processed_page_ids:
                        print(f"  Skipping already processed page: {page.get('title')}")
                        continue
                    
                    total_pages += 1
                    print(f"  Processing page {page_index}/{len(pages_to_process)} ({total_pages} total): {page.get('title')} (ID: {page.get('id')})")
                    
                    try:
                        # Get full page content
                        page_data = client.get_page_content(page.get('id'))
                        if page_data:
                            # Add space information to the page data
                            page_data['space_name'] = space.get('name')
                            page_data['space_key'] = space.get('key')
                            if create_confluence_node(session, page_data):
                                successful_pages += 1
                                processed_page_ids.add(page.get('id'))
                        
                        # Check for child pages
                        child_pages_data = client.get_child_pages(page.get('id'))
                        child_pages = child_pages_data.get('results', [])
                        if child_pages:
                            print(f"    Found {len(child_pages)} child pages for {page.get('title')}")
                            # Add these pages to our processing queue
                            pages_to_process.extend(child_pages)
                    except Exception as e:
                        print(f"  ERROR processing page {page.get('title', 'Unknown')}: {str(e)}")
            
            except Exception as e:
                print(f"ERROR processing space {space.get('name', 'Unknown')}: {str(e)}")
        
        print(f"\nSummary: Processed {total_pages} pages from {total_spaces} spaces")
        print(f"Successfully created {successful_pages} nodes in Neo4j")
    
    return successful_pages > 0

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