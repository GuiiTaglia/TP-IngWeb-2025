from django.shortcuts import render
from haystack import indexes
from haystack.query import SearchQuerySet
from bullet_journal.models import Journal

class JournalIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title', null=True)
    entry = indexes.CharField(model_attr='entry', null=True)

    def get_model(self):
        return Journal

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

def search(request):
    query = request.GET.get('q', '')
    results = SearchQuerySet().filter(content=query) if query else []
    return render(request, 'search/search.html', {
        'query': query,
        'page': results,
    })


