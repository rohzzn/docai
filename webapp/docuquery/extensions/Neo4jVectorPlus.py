import traceback
import logging
from langchain_community.vectorstores.neo4j_vector import Neo4jVector
import enum
from typing import (
    Any,
    List,
    Optional,
    Type,
)

from langchain_core.embeddings import Embeddings


class SearchType(str, enum.Enum):
    """Enumerator of the Distance strategies."""

    VECTOR = "vector"
    HYBRID = "hybrid"


DEFAULT_SEARCH_TYPE = SearchType.VECTOR


class Neo4jVectorPlus(Neo4jVector):

    @classmethod
    def from_existing_graph(
        cls: Type[Neo4jVector],
        embedding: Embeddings,
        node_label: str,
        embedding_node_property: str,
        text_node_properties: List[str],
        create_embeddings: bool = False,
        *,
        keyword_index_name: Optional[str] = "keyword",
        index_name: str = "vector",
        search_type: SearchType = DEFAULT_SEARCH_TYPE,
        retrieval_query: str = "",
        **kwargs: Any,
    ) -> Neo4jVector:
        """
        Initialize and return a Neo4jVector instance from an existing graph.

        This method initializes a Neo4jVector instance using the provided
        parameters and the existing graph. It validates the existence of
        the indices and creates new ones if they don't exist.

        Returns:
        Neo4jVector: An instance of Neo4jVector initialized with the provided parameters
                    and existing graph.

        Example:
        >>> neo4j_vector = Neo4jVector.from_existing_graph(
        ...     embedding=my_embedding,
        ...     node_label="Document",
        ...     embedding_node_property="embedding",
        ...     text_node_properties=["title", "content"]
        ... )

        Note:
        Neo4j credentials are required in the form of `url`, `username`, and `password`,
        and optional `database` parameters passed as additional keyword arguments.
        """
        try:
            # Validate the list is not empty
            if not text_node_properties:
                raise ValueError(
                    "Parameter `text_node_properties` must not be an empty list"
                )
            # Prefer retrieval query from params, otherwise construct it
            if not retrieval_query:
                retrieval_query = (
                    f"RETURN reduce(str='', k IN {text_node_properties} |"
                    " str + '\\n' + k + ': ' + coalesce(node[k], '')) AS text, "
                    "node {.*, `"
                    + embedding_node_property
                    + "`: Null, id: Null, "
                    + ", ".join([f"`{prop}`: Null" for prop in text_node_properties])
                    + "} AS metadata, score"
                )
            
            # Log connection parameters (without credentials)
            logging.info(f"Connecting to Neo4j with node_label={node_label}, index_name={index_name}")
            
            store = cls(
                embedding=embedding,
                index_name=index_name,
                keyword_index_name=keyword_index_name,
                search_type=search_type,
                retrieval_query=retrieval_query,
                node_label=node_label,
                embedding_node_property=embedding_node_property,
                **kwargs,
            )

            # Check if the vector index already exists
            embedding_dimension, index_type = store.retrieve_existing_index()
            
            logging.info(f"Retrieved existing index: dimension={embedding_dimension}, type={index_type}")

            # Raise error if relationship index type
            if index_type == "RELATIONSHIP":
                raise ValueError(
                    "`from_existing_graph` method does not support "
                    " existing relationship vector index. "
                    "Please use `from_existing_relationship_index` method"
                )

            # If the vector index doesn't exist yet
            if not embedding_dimension:
                logging.info(f"Creating new vector index: {index_name}")
                store.create_new_index()
            # If the index already exists, check if embedding dimensions match
            elif not store.embedding_dimension == embedding_dimension:
                raise ValueError(
                    f"Index with name {store.index_name} already exists."
                    "The provided embedding function and vector index "
                    "dimensions do not match.\n"
                    f"Embedding function dimension: {store.embedding_dimension}\n"
                    f"Vector index dimension: {embedding_dimension}"
                )
                
            # FTS index for Hybrid search
            if search_type == SearchType.HYBRID:
                fts_node_label = store.retrieve_existing_fts_index(text_node_properties)
                # If the FTS index doesn't exist yet
                if not fts_node_label:
                    logging.info(f"Creating new keyword index: {keyword_index_name}")
                    store.create_new_keyword_index(text_node_properties)
                else:  # Validate that FTS and Vector index use the same information
                    if not fts_node_label == store.node_label:
                        raise ValueError(
                            "Vector and keyword index don't index the same node label"
                        )

            # Populate embeddings
            if create_embeddings:
                logging.info("Populating embeddings for nodes without embeddings")
                nodes_processed = 0
                
                while True:
                    fetch_query = (
                        f"MATCH (n:`{node_label}`) "
                        f"WHERE n.{embedding_node_property} IS null "
                        "AND any(k in $props WHERE n[k] IS NOT null) "
                        f"RETURN elementId(n) AS id, reduce(str='',"
                        "k IN $props | str + '\\n' + k + ':' + coalesce(n[k], '')) AS text "
                        "LIMIT 1000"
                    )
                    data = store.query(fetch_query, params={"props": text_node_properties})
                    
                    if not data:
                        logging.info("No more nodes to embed")
                        break
                        
                    batch_size = len(data)
                    nodes_processed += batch_size
                    logging.info(f"Embedding batch of {batch_size} nodes")
                    
                    text_embeddings = embedding.embed_documents([el["text"] for el in data])

                    params = {
                        "data": [
                            {"id": el["id"], "embedding": embedding}
                            for el, embedding in zip(data, text_embeddings)
                        ]
                    }

                    store.query(
                        "UNWIND $data AS row "
                        f"MATCH (n:`{node_label}`) "
                        "WHERE elementId(n) = row.id "
                        f"CALL db.create.setVectorProperty(n, "
                        f"'{embedding_node_property}', row.embedding) "
                        "YIELD node RETURN count(*)",
                        params=params,
                    )
                    
                    # If embedding calculation should be stopped
                    if len(data) < 1000:
                        break
                        
                logging.info(f"Completed embedding process for {nodes_processed} nodes")
                
            return store
            
        except Exception as e:
            logging.error(f"Error in Neo4jVectorPlus.from_existing_graph: {str(e)}")
            logging.error(traceback.format_exc())
            raise
