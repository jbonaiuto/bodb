import datetime
from haystack import indexes
from bodb.models import *

class DocumentFigureIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return DocumentFigure

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
    

class DocumentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Document

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
    
class ModelIndex(DocumentIndex):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Model

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