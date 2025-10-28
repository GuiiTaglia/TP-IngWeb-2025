from django.shortcuts import render
from haystack.query import SearchQuerySet


def search(request):
    query = request.GET.get('q', '')
    results = SearchQuerySet().filter(content=query) if query else []
    return render(request, 'search/search.html', {
        'query': query,
        'page': results,
    })


