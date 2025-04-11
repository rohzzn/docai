from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

# from docuquery.graph.DocuQuery import DocuQuery
from docuquery.graph.DocuQueryMultiRetriever import DocuQuery


@require_http_methods(["GET"])
def index(request):
    return HttpResponse("Hello, world!")

@require_http_methods(["GET"])
def search(request):
    query = request.GET.get('q', '')
    docuquery = DocuQuery()
    response = docuquery.invoke({"query": query, "username": "JaneSmith"})

    parsed_document = []
    for document in response.get("relevant_documents"):
        data = DocuQuery.parse_document_content(document.page_content)
        parsed_document.append({**data, **document.metadata})

    response_data = {
        "answer": response.get("final_response"),
        "postgres_rows": response.get("postgres_rows"),
        "query": query,
        "relevant_documents": parsed_document,
    }
    return JsonResponse(response_data)




