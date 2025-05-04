#!/usr/bin/env python3
import os
import sys
from neo4j import GraphDatabase
import openai
from pathlib import Path

# Get the absolute path to the webapp directory
current_dir = Path(__file__).resolve().parent
webapp_dir = current_dir / "webapp"

# Add webapp to system path
sys.path.append(str(webapp_dir))

# Neo4j database credentials
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "root@neo4j"

# Set up OpenAI for embeddings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-your-openai-api-key")
openai.api_key = OPENAI_API_KEY

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Sample documents to add to Neo4j
confluence_documents = [
    {
        "id": "rdcrn-overview-doc",
        "title": "RDCRN Overview", 
        "text": """
The Rare Diseases Clinical Research Network (RDCRN) is a collaborative network of research centers and patient advocacy groups dedicated to advancing medical research on rare diseases. 
Funded by the National Institutes of Health (NIH), the RDCRN aims to improve the diagnosis, treatment, and overall care for individuals with rare diseases.

Key aspects of RDCRN:
1. It consists of multiple clinical research consortia, each focused on a group of related rare diseases
2. It includes a Data Management and Coordinating Center (DMCC) that provides centralized support
3. It collaborates with patient advocacy groups to ensure research addresses patient needs
4. It conducts multisite clinical research studies to gather sufficient data on rare conditions
5. It provides training opportunities for clinical researchers interested in rare disease research

The RDCRN has been instrumental in developing new treatments, diagnostic tools, and clinical care guidelines for numerous rare diseases.
        """
    },
    {
        "id": "rdcrn-data-sharing-doc",
        "title": "RDCRN Data Sharing Policies",
        "text": """
The Rare Diseases Clinical Research Network (RDCRN) has established comprehensive data sharing policies to facilitate collaboration while ensuring data security and patient privacy.

Data sharing within the RDCRN follows these principles:
1. All data is de-identified to protect patient privacy before sharing
2. Researchers must submit formal data requests that are reviewed by a data access committee
3. Data use agreements must be signed before access is granted
4. Different access levels exist depending on the sensitivity of the data
5. Cloud-based secure environments are used for accessing and analyzing sensitive data

The RDCRN Cloud Environment provides a secure platform for researchers to access and analyze data without downloading raw data to local systems. This approach balances the need for collaborative research with the requirements for data protection.

For more information about accessing RDCRN data, researchers should contact the Data Management and Coordinating Center (DMCC).
        """
    },
    {
        "id": "rare-disease-research-doc",
        "title": "Rare Disease Research Challenges",
        "text": """
Conducting research on rare diseases presents unique challenges that require specialized approaches and collaborative efforts.

Major challenges in rare disease research include:
1. Small patient populations make traditional clinical trials difficult
2. Geographic dispersion of patients requires multi-center collaboration
3. Limited natural history data for many conditions
4. Heterogeneity within disease groups complicates study design
5. Funding limitations for conditions affecting small populations
6. Regulatory pathways that may not be optimized for rare disease treatments

The RDCRN addresses these challenges through:
- Networked research centers that can collectively recruit sufficient patients
- Patient registries and natural history studies to build foundational knowledge
- Novel clinical trial designs adapted for small populations
- Collaborative funding models involving government, industry, and patient organizations
- Engagement with regulatory agencies to develop appropriate approval pathways

Despite these challenges, significant progress has been made in rare disease research, leading to new diagnostic methods and treatments for many previously untreatable conditions.
        """
    }
]

# Function to get embeddings from OpenAI
def get_embedding(text):
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
        # Return a small random embedding as fallback
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

def create_confluence_nodes(session, documents):
    for doc in documents:
        # Generate embedding for the document text
        text_for_embedding = f"{doc['title']} {doc['text']}"
        embedding = get_embedding(text_for_embedding)
        
        # Create node in Neo4j
        session.run("""
        CREATE (n:Confluence {
            id: $id,
            title: $title,
            text: $text,
            embedding: $embedding
        })
        """, id=doc["id"], title=doc["title"], text=doc["text"], embedding=embedding)
        
        print(f"Created node for document: {doc['title']}")

def main():
    with driver.session() as session:
        # Clear existing data and create indexes
        clear_existing_data(session)
        create_indexes(session)
        
        # Create nodes for sample documents
        create_confluence_nodes(session, confluence_documents)
        
        # Verify data was added
        result = session.run("MATCH (n:Confluence) RETURN count(n) as count")
        count = result.single()["count"]
        print(f"Successfully added {count} documents to Neo4j")

if __name__ == "__main__":
    main()
    driver.close() 