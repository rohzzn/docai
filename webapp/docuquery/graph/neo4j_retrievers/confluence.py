import os
import requests
import json
from pathlib import Path
from .base import Neo4jBaseRetriever

EMBEDDING_NODE_LABEL="Confluence"
INDEX_NAME = "confluence_embedding"
KEYWORD_INDEX_NAME = "confluence_keyword"

def get_text_embeddable_columns():
    return ["id", "text", "title", "space_name", "space_key"]

class SimpleConfluenceClient:
    def __init__(self):
        self.baseURL = os.environ.get("CONFLUENCE_BASE_URL", "https://rdcrn.atlassian.net/wiki")
        self.accessToken = os.environ.get("CONFLUENCE_ACCESS_TOKEN")
        self.refreshToken = os.environ.get("CONFLUENCE_REFRESH_TOKEN")
        self.clientId = os.environ.get("CONFLUENCE_CLIENT_ID")
        self.clientSecret = os.environ.get("CONFLUENCE_CLIENT_SECRET")
        
        self.headers = {
            'Authorization': f'Bearer {self.accessToken}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def getSpaces(self):
        url = f"{self.baseURL}/api/v2/spaces"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def getPages(self, spaceId):
        url = f"{self.baseURL}/api/v2/pages"
        params = {'spaceId': spaceId}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def getPageContent(self, pageId):
        # First get the page metadata using v2 API
        url = f"{self.baseURL}/api/v2/pages/{pageId}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        # Then get the page content using v1 API
        content_url = f"{self.baseURL}/rest/api/content/{pageId}"
        params = {'expand': 'body.storage,space,version'}
        content_response = requests.get(content_url, headers=self.headers, params=params)
        content_response.raise_for_status()
        
        # Combine the metadata with the content
        pageData = {
            **response.json(),
            'content': content_response.json()
        }
        
        return pageData

class Neo4jConfluenceRetriever(Neo4jBaseRetriever):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_name = INDEX_NAME
        self.keyword_index_name = KEYWORD_INDEX_NAME
        self.embedding_node_label = EMBEDDING_NODE_LABEL
        self.embedding = self.embedding
        self.text_embeddable_columns = get_text_embeddable_columns()
        
        # Initialize Confluence client
        try:
            self.client = SimpleConfluenceClient()
            print("Confluence client initialized successfully")
        except Exception as e:
            print(f"Error initializing Confluence client: {str(e)}")
            self.client = None

