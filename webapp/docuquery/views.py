from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
import logging
import traceback
import re
import json
import socket

# from docuquery.graph.DocuQuery import DocuQuery
from docuquery.graph.DocuQueryMultiRetriever import DocuQuery


@require_http_methods(["GET"])
def index(request):
    return HttpResponse("Hello, world!")

@require_http_methods(["GET"])
def api_status(request):
    """
    Diagnostic endpoint to check API connectivity and server information
    """
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        
        status_data = {
            "status": "ok",
            "message": "API is working correctly",
            "server_info": {
                "hostname": hostname,
                "ip": ip,
                "headers": dict(request.headers),
                "host": request.get_host(),
                "method": request.method,
                "path": request.path,
            }
        }
        return JsonResponse(status_data)
    except Exception as e:
        logging.error(f"Status check error: {str(e)}")
        return JsonResponse({"status": "error", "error": str(e)}, status=500)

@require_http_methods(["GET"])
def search(request):
    query = request.GET.get('q', '')
    try:
        docuquery = DocuQuery()
        response = docuquery.invoke({"query": query, "username": "JaneSmith"})

        parsed_document = []
        for document in response.get("relevant_documents", []):
            # Parse the document content
            data = DocuQuery.parse_document_content(document.page_content)
            
            # Get the metadata
            metadata = document.metadata
            
            # If text field is empty, use the raw page content with field names stripped
            if not data.get("text"):
                # Extract text by removing known field patterns
                page_text = document.page_content
                # Remove id:, title:, and data_source: patterns
                page_text = re.sub(r'id:"[^"]*"\s*', '', page_text)
                page_text = re.sub(r'title:"[^"]*"\s*', '', page_text)
                page_text = re.sub(r'data_source:"[^"]*"\s*', '', page_text)
                page_text = page_text.strip()
                data["text"] = page_text
            
            # Create a clean document structure
            clean_doc = {
                "id": data.get("id", metadata.get("id", "")),
                "title": data.get("title", metadata.get("title", "")),
                "data_source": metadata.get("data_source", ""),
                # Ensure 'text' field doesn't contain metadata fields
                "text": data.get("text", ""),
                # Add space information
                "space_name": data.get("space_name", metadata.get("space_name", "")),
                "space_key": data.get("space_key", metadata.get("space_key", "")),
            }
            
            parsed_document.append(clean_doc)

        response_data = {
            "answer": response.get("final_response"),
            "postgres_rows": response.get("postgres_rows"),
            "query": query,
            "relevant_documents": parsed_document,
        }
        return JsonResponse(response_data)
    except Exception as e:
        logging.error(f"Search error for query '{query}': {str(e)}")
        logging.error(traceback.format_exc())
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500) 