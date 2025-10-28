from django.shortcuts import render
from haystack.query import SearchQuerySet


def search(request):
    query = request.GET.get('q', '')
    results = [r.object for r in SearchQuerySet().filter(content=query) if r.object.title or r.object.diary_entry] if query else []
    return render(request, 'search/search.html', {
        'query': query,
        'page': results,
    })


