from .base import Neo4jBaseRetriever

EMBEDDING_NODE_LABEL="Confluence"
INDEX_NAME = "confluence_embedding"
KEYWORD_INDEX_NAME = "confluence_keyword"

def get_text_embeddable_columns():
    return ["id", "text", "title"]

class Neo4jConfluenceRetriever(Neo4jBaseRetriever):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_name = INDEX_NAME
        self.keyword_index_name = KEYWORD_INDEX_NAME
        self.embedding_node_label = EMBEDDING_NODE_LABEL
        self.embedding = self.embedding
        self.text_embeddable_columns = get_text_embeddable_columns()

