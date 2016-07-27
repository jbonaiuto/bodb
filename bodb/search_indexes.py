import datetime
from haystack import indexes
from bodb.models import *


class DocumentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Document

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
    
    
class SEDIndex(DocumentIndex):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return SED

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()