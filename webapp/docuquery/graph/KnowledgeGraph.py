import os
import sys
import logging

from langchain_community.document_loaders import ConfluenceLoader
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from docuquery.constants.app import DEFAULT_MODEL_NAME
from docuquery.constants.neo4j import (
    USERNAME,
    PASSWORD,
    URL,
)

import nest_asyncio
nest_asyncio.apply()


RDCRN_CONFLUENCE_SPACE = os.environ.get("RDCRN_CONFLUENCE_SPACE")
RDCRN_CONFLUENCE_URL = os.environ.get("RDCRN_CONFLUENCE_URL")

# Log environment variables for debugging
logging.info(f"RDCRN_CONFLUENCE_SPACE: {RDCRN_CONFLUENCE_SPACE}")
logging.info(f"RDCRN_CONFLUENCE_URL: {RDCRN_CONFLUENCE_URL}")

def main():
    url = RDCRN_CONFLUENCE_URL
    space_key = RDCRN_CONFLUENCE_SPACE
    loader = ConfluenceLoader(
        cloud=True,
        space_key=space_key,
        url=url,
    )

    documents = loader.load()
    documents = list(filter(lambda x: x.page_content, documents))

    llm = ChatOpenAI(temperature=0, model_name=DEFAULT_MODEL_NAME)
    llm_transformer = LLMGraphTransformer(llm=llm)
    graph_documents = llm_transformer.convert_to_graph_documents(documents)

    graph = Neo4jGraph(url=URL, username=USERNAME, password=PASSWORD)
    graph.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,
        include_source=True
    )

if __name__ == "__main__":
    main()