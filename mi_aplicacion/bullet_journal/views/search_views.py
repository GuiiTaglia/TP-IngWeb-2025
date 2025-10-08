from django.shortcuts import render
from haystack.query import SearchQuerySet

def search(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = SearchQuerySet().filter(content=query)
    return render(request, 'search/search.html', {'results': results, 'query': query})