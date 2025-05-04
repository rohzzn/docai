import os
import re
import sys
import html

from typing_extensions import TypedDict
from typing import List

from langchain_core.runnables import RunnableParallel

from langchain.prompts import PromptTemplate

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import END, StateGraph

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from docuquery.graph.neo4j_retrievers.confluence import Neo4jConfluenceRetriever
from docuquery.graph.neo4j_retrievers.postgres import Neo4jPostgresRetriever

from docuquery.constants.app import DEFAULT_MODEL_NAME

class GraphState(TypedDict):

    """
    Represents the state of our graph.

    Attributes:
        accessible_documents: List of documents that the user has access to
        final_response: LLM generated answer
        relevant_documents: List of accessible documents relevant to user query
        retrieved_documents: List of documents fetched initially after vector search
        user_query: User query
        username: Username
    """
    accessible_documents: List[str]
    final_response: str
    relevant_documents: List[str]
    retrieved_documents: List[str]
    user_query: str
    username: str

def decide_to_proceed_permission(state):
    if "final_response" in state and state.get("final_response"):
        return "no_documents"
    return "has_documents"

def decide_to_proceed_relevancy(state):
    if "final_response" in state and state.get("final_response"):
        return "no_documents"
    return "has_documents"

def generate_answer(state):
    """
    Generate answer using RAG on retrieved documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """

    prompt_template = """
    You are an intelligent assistant that provides answers based on the given contextual data.
    
    Given the following input:
    - Query: {query}
    - Neo4j Documents: {neo4j_documents}
    
    Please provide a complete and direct answer to the query using only the information from the context provided.
    
    **Important**:
    - Only use information from the context.
    - Do not include any reasoning, explanations, or document names unless specifically required for the answer.
    """

    # Fix the initialization of ChatOpenAI
    import os
    # Ensure OPENAI_API_KEY is set
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "sk-your-openai-api-key")
    
    # Import OpenAI directly to avoid class definition issues
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    # Create a direct implementation to generate answer
    def generate_response(query, neo4j_documents):
        prompt_text = prompt_template.format(query=query, neo4j_documents=neo4j_documents)
        response = client.chat.completions.create(
            model=DEFAULT_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an intelligent assistant that provides answers based on the given contextual data."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0
        )
        return response.choices[0].message.content
    
    print("---GENERATE---")
    neo4j_documents = state.get("relevant_documents")
    user_query = state.get("user_query")
    
    generated_response = generate_response(user_query, neo4j_documents)
    return {"final_response": generated_response}

def permission_check(state):
    """
    Determines whether the user has permissions to the retrieved documents.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with the documents user has access to
    """

    retrieved_documents = state.get("retrieved_documents")
    username = state.get("username")

    accessible_documents = []
    updated_state = {}
    for document in retrieved_documents:
        shared_with_users = document.metadata.get("sharedWithUsers")

        if not shared_with_users or username in shared_with_users:
            print("---GRADE: DOCUMENT ACCESSIBLE---")
            accessible_documents.append(document)
        else:
            print("---GRADE: DOCUMENT NOT ACCESSIBLE---")

    updated_state["accessible_documents"] = accessible_documents
    if not accessible_documents:
        updated_state["final_response"] = "You don't have access to the relevant documents."

    return updated_state

def relevancy_check(state):
    """
    Determines whether the accessible documents are relevant to the user query.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with relevant accessible documents
    """
    prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user query. \n 
            Here is the retrieved document: \n\n {context} \n\n
            Here is the user query: {query} \n
            If the document contains keywords related to the user query, grade it as relevant. \n
            It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the query. \n
            Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.""",
        input_variables=["query", "context"],
    )

    # Fix the initialization of ChatOpenAI
    import os
    # Ensure OPENAI_API_KEY is set
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "sk-your-openai-api-key")
    
    # Import OpenAI directly to avoid class definition issues
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    # Create a simple function to mimic ChatOpenAI
    def ask_openai(prompt_text):
        response = client.chat.completions.create(
            model=DEFAULT_MODEL_NAME,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0
        )
        return response.choices[0].message.content
    
    # Use a simple chain with the custom OpenAI function
    def chain_invoke(inputs):
        context = inputs.get("context", "")
        query = inputs.get("query", "")
        prompt_text = prompt.template.format(context=context, query=query)
        response = ask_openai(prompt_text)
        # Parse the JSON response
        import json
        try:
            return json.loads(response)
        except:
            # Fallback if JSON parsing fails
            if "yes" in response.lower():
                return {"score": "yes"}
            else:
                return {"score": "no"}
    
    # Use our custom chain instead of the LangChain one
    chain = chain_invoke

    accessible_documents = state.get("accessible_documents")
    query = state.get("user_query")

    relevant_documents = []
    for document in accessible_documents:
        score = chain({
            "context": f'{document.page_content} \n\n{str(document.metadata)}',
            "query": query,
        })
        if score["score"] == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            relevant_documents.append(document)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")

    updated_state = {"relevant_documents": relevant_documents}
    if not relevant_documents:
        updated_state["final_response"] = "No relevant document found."

    return updated_state

def retrieve_documents(state):
    """
    Retrieve documents from vectorstore

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """

    neo4j_pr = Neo4jPostgresRetriever()
    postgres_document_retriever = neo4j_pr.get_document_retriever()

    neo4j_cr = Neo4jConfluenceRetriever()
    confluence_document_retriever = neo4j_cr.get_document_retriever()

    print("---NEO4J RETRIEVE---")
    query = state.get("user_query")

    parallel_retriever = RunnableParallel(
        postgres=postgres_document_retriever,
        confluence=confluence_document_retriever
    )

    results = parallel_retriever.invoke(query)

    for doc in results['postgres']:
        # Add data_source to metadata instead of page_content
        doc.metadata['data_source'] = 'postgres'

    for doc in results['confluence']:
        # Add data_source to metadata instead of page_content
        doc.metadata['data_source'] = 'confluence'

    retrieved_documents = results['postgres'] + results['confluence']

    return {"retrieved_documents": retrieved_documents}

class DocuQuery:
    def __init__(self):
        self.graph = DocuQuery.get_graph()

    def invoke(self, data):
        return self.graph.invoke({
            "user_query": data.get("query"),
            "username": "JaneSmith",
        })

    @staticmethod
    def get_graph():
        workflow = StateGraph(GraphState)

        # Define the nodes
        workflow.add_node("generate_answer", generate_answer)
        workflow.add_node("permission_check", permission_check)
        workflow.add_node("relevancy_check", relevancy_check)
        workflow.add_node("retrieve_documents", retrieve_documents)

        # Build graph
        workflow.set_entry_point("retrieve_documents")
        workflow.add_edge("retrieve_documents", "permission_check")

        workflow.add_conditional_edges(
            "permission_check",
            decide_to_proceed_permission,
            {
                "no_documents": END,
                "has_documents": "relevancy_check",
            }
        )

        workflow.add_conditional_edges(
            "relevancy_check",
            decide_to_proceed_relevancy,
            {
                "no_documents": END,
                "has_documents": "generate_answer",
            }
        )
        workflow.add_edge("generate_answer", END)

        return workflow.compile()

    @staticmethod
    def parse_document_content(page_content):
        properties = {}
        
        # Remove any trailing data_source field if it exists
        content_lines = []
        data_source = None
        
        for line in page_content.strip().split('\n'):
            if line.strip().startswith('data_source:'):
                continue
            content_lines.append(line)
                
        # Parse the content    
        for line in content_lines:
            key_value = line.split(':', 1)
            if len(key_value) == 2:
                key = key_value[0].strip()
                value = key_value[1].strip()
                if value and key not in ['data_source']:
                    # Decode HTML entities like &rsquo; and &nbsp;
                    properties[key] = html.unescape(value)

        return properties


if __name__ == '__main__':
    docuquery = DocuQuery()
    response = docuquery.invoke({
        "query": "tell me about Encephalomyopathy?",
        "username": "JaneSmith"
    })
    parsed_document = []
    for document in response.get("relevant_documents"):
        data = DocuQuery.parse_document_content(document.page_content)
        print(data)

        parsed_document.append({**data, **document.metadata})
    # print(parsed_document)

