from bullet_journal.models import Journal
from haystack import indexes

class DiarioIndex(indexes.SearchIndex, indexes.Indexable):
    title = indexes.CharField(model_attr='title')
    entry = indexes.CharField(model_attr='entry')

    def get_model(self):
        return Journal

    def index_queryset(self, using=None):
        return self.get_model().objects.all()