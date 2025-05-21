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
    You are an intelligent assistant that provides direct, concise answers.
    
    Given the following input:
    - User Query: {query}
    - Documents: {neo4j_documents}
    
    Please provide an accurate answer to the query based on the information from the provided documents.
    
    **Important Guidelines**:
    1. Provide direct answers without repeating the question.
    2. Don't use phrases like "Based on the provided documents" or "According to the information".
    3. For common acronyms, organizations, or terms (like NIH, RDCRN, etc.) that appear in the documents but aren't fully defined, you may provide standard definitions or expansions.
    4. Make reasonable inferences from the information in the documents when appropriate.
    5. If the documents mention a concept but don't fully explain it, you may provide basic clarification using widely known information.
    6. If the documents contain only partial information about the query, provide what you can without acknowledging limitations.
    7. If no information is available, simply say "No information available about this topic."
    8. Structure your answer using proper markdown formatting:
       - Use ## for section headings
       - Use **bold** for emphasis
       - Use - or * for bullet points
       - Use 1., 2., etc. for numbered lists
       - Use [text](url) format for links
       - Use proper paragraph breaks with empty lines
    """

    # Fix the initialization of ChatOpenAI
    import os
    import logging
    
    # Ensure OPENAI_API_KEY is set
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "sk-your-openai-api-key")
    
    # Import OpenAI directly to avoid class definition issues
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    # Create a direct implementation to generate answer
    def generate_response(query, neo4j_documents):
        # Debug logging
        print(f"DEBUG: Got query: '{query}'")
        print(f"DEBUG: Documents count: {len(neo4j_documents)}")
        
        # Check if documents have content
        docs_with_content = []
        for i, doc in enumerate(neo4j_documents):
            content_length = len(str(doc.page_content)) if hasattr(doc, 'page_content') else 0
            print(f"DEBUG: Document content length: {content_length}")
            if content_length > 0:
                docs_with_content.append(doc)
                # Print a snippet of the document content for debugging
                print(f"Doc {i+1}: Document Title: {doc.metadata.get('title', 'Unknown')}")
                content_preview = doc.page_content[:20] + "..." if len(doc.page_content) > 20 else doc.page_content
                print(f"Document Content: {content_preview}")
        
        if not docs_with_content:
            print("DEBUG: No documents with valid content found")
            return "Based on the available information, I cannot provide a complete answer to this question."
        
        print(f"DEBUG: In generate_response - Documents have content: {len(docs_with_content) > 0}")
        print(f"---USING {len(docs_with_content)} DOCUMENTS FOR ANSWER GENERATION---")
        
        # Prepare document text for prompt
        formatted_docs = []
        for i, doc in enumerate(docs_with_content):
            doc_text = f"Document {i+1}:\n"
            if hasattr(doc, 'metadata') and doc.metadata:
                doc_text += f"Title: {doc.metadata.get('title', 'Untitled')}\n"
            doc_text += f"Content: {doc.page_content}\n"
            formatted_docs.append(doc_text)
        
        documents_text = "\n".join(formatted_docs)
        
        # Generate response
        prompt_text = prompt_template.format(query=query, neo4j_documents=documents_text)
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are an intelligent assistant that provides direct, concise answers without preamble."},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"ERROR generating response: {str(e)}")
            return "Sorry, I encountered an error while generating a response. Please try again."

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
        template="""You are evaluating whether a document is relevant to a user query.

Document content: 
{context}

User query: {query}

Your task is to determine if this document contains any information that might help answer the query.
Even if the document only partially addresses the query or contains related information, it should be considered relevant.
Only mark documents as not relevant if they are completely unrelated to the query topic.

Please respond with "yes" if the document is even slightly relevant, and "no" only if it is completely unrelated.
Provide your answer as a JSON with a single key "score" and value "yes" or "no" with no additional explanation.""",
        input_variables=["query", "context"],
    )

    # Fix the initialization of ChatOpenAI
    import os
    import logging
    
    # Ensure OPENAI_API_KEY is set
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "sk-your-openai-api-key")
    
    # Import OpenAI directly to avoid class definition issues
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    # Create a simple function to mimic ChatOpenAI
    def ask_openai(prompt_text):
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL_NAME,
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in ask_openai: {str(e)}")
            # Default to yes if there's an error, to be more inclusive
            return '{"score": "yes"}'
    
    # Use a simple chain with the custom OpenAI function
    def chain_invoke(inputs):
        context = inputs.get("context", "")
        query = inputs.get("query", "")
        prompt_text = prompt.template.format(context=context, query=query)
        response = ask_openai(prompt_text)
        # Parse the JSON response
        import json
        try:
            # Remove any Markdown formatting that might be present in the response
            clean_response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_response)
        except Exception as e:
            logging.error(f"Error parsing JSON: {str(e)}, response: {response}")
            # Fallback if JSON parsing fails
            if "yes" in response.lower():
                return {"score": "yes"}
            else:
                return {"score": "no"}
    
    # Use our custom chain instead of the LangChain one
    chain = chain_invoke

    accessible_documents = state.get("accessible_documents")
    query = state.get("user_query")

    # If no documents, return early
    if not accessible_documents or len(accessible_documents) == 0:
        print("---NO ACCESSIBLE DOCUMENTS FOUND---")
        return {"relevant_documents": [], "final_response": "No relevant documents found."}

    # Keep track of relevant documents
    relevant_documents = []
    
    # Print query for debugging
    print(f"---EVALUATING RELEVANCE FOR QUERY: {query}---")
    
    for i, document in enumerate(accessible_documents):
        # Extract document info for logging
        doc_id = document.metadata.get('id', f'doc_{i}')
        doc_title = document.metadata.get('title', 'Untitled')
        
        # Get the first 200 characters for preview
        content_preview = document.page_content[:200] + "..." if len(document.page_content) > 200 else document.page_content
        print(f"---DOCUMENT {i+1}: {doc_title} ({doc_id})---")
        print(f"---CONTENT PREVIEW: {content_preview}---")
        
        # Perform relevance check
        try:
            score = chain({
                "context": f'{document.page_content} \n\n{str(document.metadata)}',
                "query": query,
            })
            
            if score.get("score") == "yes":
                print(f"---GRADE: DOCUMENT RELEVANT---")
                relevant_documents.append(document)
            else:
                print(f"---GRADE: DOCUMENT NOT RELEVANT---")
        except Exception as e:
            # If there's an error in relevancy check, include the document (be more permissive)
            print(f"---ERROR IN RELEVANCY CHECK: {str(e)}, INCLUDING DOCUMENT---")
            relevant_documents.append(document)

    # Update state with relevant documents
    updated_state = {"relevant_documents": relevant_documents}
    
    # If no relevant documents were found, set a clear message
    if not relevant_documents:
        print("---NO RELEVANT DOCUMENTS FOUND---")
        updated_state["final_response"] = "No information available about this topic."
    else:
        print(f"---FOUND {len(relevant_documents)} RELEVANT DOCUMENTS---")

    return updated_state

def retrieve_documents(state):
    """
    Retrieve documents from vectorstore

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """

    print("---NEO4J RETRIEVE---")
    query = state.get("user_query")

    try:
        # Try to connect to Neo4j and retrieve documents
        neo4j_cr = Neo4jConfluenceRetriever()
        confluence_document_retriever = neo4j_cr.get_document_retriever()
        
        # Use only the confluence retriever
        results = {'confluence': confluence_document_retriever.invoke(query), 'postgres': []}
        
        # No Postgres documents to process
        
        for doc in results['confluence']:
            # Add data_source to metadata instead of page_content
            doc.metadata['data_source'] = 'confluence'
    
        retrieved_documents = results['confluence']
        
        return {"retrieved_documents": retrieved_documents}
    
    except Exception as e:
        # Log the error for debugging
        import logging
        logging.error(f"Error retrieving documents from Neo4j: {str(e)}")
        print(f"ERROR: Failed to retrieve documents: {str(e)}")
        
        # Return an empty result with error message
        return {
            "retrieved_documents": [], 
            "final_response": "Sorry, I'm having trouble connecting to the document database. Please check the Neo4j connection."
        }

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

