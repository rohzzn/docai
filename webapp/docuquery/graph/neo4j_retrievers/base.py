from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
import logging

from docuquery.constants.neo4j import (
    USERNAME,
    PASSWORD,
    URL,
    EMBEDDING_NODE_PROPERTY,
)
from docuquery.constants.embedding import OLLAMA_BASE_URL, EMBEDDING_MODEL_NAME
from docuquery.extensions.Neo4jVectorPlus import Neo4jVectorPlus, SearchType



class Neo4jBaseRetriever:
    def __init__(self, embedding='openai'):
        self.index_name = ''
        self.keyword_index_name = ''
        self.embedding_node_label = ''
        self.embedding = embedding
        self.text_embeddable_columns = []

    def get_document_retriever(self):
        if self.embedding == 'openai':
            embeddings = OpenAIEmbeddings()
        else:
            embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME, base_url=OLLAMA_BASE_URL)

        try:
            logging.info(f"Creating vector store with node label: {self.get_embedding_node_label()}, index: {self.get_index_name()}")
            vector_store = Neo4jVectorPlus.from_existing_graph(
                embeddings,
                url=URL,
                username=USERNAME,
                password=PASSWORD,
                index_name=self.get_index_name(),
                keyword_index_name=self.get_keyword_index_name(),
                node_label=self.get_embedding_node_label(),
                text_node_properties=self.text_embeddable_columns,
                embedding_node_property=EMBEDDING_NODE_PROPERTY,
                search_type=SearchType.HYBRID,
                create_embeddings=True,
            )
            
            # Configure the retriever for better results
            retriever = vector_store.as_retriever(
                search_kwargs={
                    "k": 5,  # Increase number of results
                    "score_threshold": 0.5,  # Set a relevance threshold
                    "fetch_k": 10  # Fetch more candidates for filtering
                }
            )
            
            # Log successful creation
            logging.info(f"Successfully created document retriever for {self.get_embedding_node_label()}")
            return retriever
            
        except Exception as e:
            logging.error(f"Error creating document retriever: {str(e)}")
            # Return a fallback retriever or raise the exception
            raise

    def get_index_name(self):
        return self.index_name

    def get_embedding_node_label(self):
        return self.embedding_node_label

    def get_keyword_index_name(self):
        return self.keyword_index_name
