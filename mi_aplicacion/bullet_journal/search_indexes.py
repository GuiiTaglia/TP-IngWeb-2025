from haystack import indexes
from .models import Journal

class JournalIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title', null=True)
    diary_entry = indexes.CharField(model_attr='diary_entry', null=True)
    username = indexes.CharField(model_attr='user__username', null=True)
    custom_habits = indexes.CharField(null=True)

    def get_model(self):
        return Journal

    def prepare_custom_habits(self, obj):
        return obj.get_custom_habits_text()

    def index_queryset(self, using=None):
        return self.get_model().objects.all()