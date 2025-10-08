from haystack import indexes
from bullet_journal.models import Journal

class JournalIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    entry = indexes.CharField(model_attr='entry')

    def get_model(self):
        return Journal

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


