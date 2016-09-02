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


class BrainImagingSEDIndex(SEDIndex):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return BrainImagingSED

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
    
    
class ConnectivitySEDIndex(SEDIndex):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return ConnectivitySED

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
    
    
class ERPSEDIndex(SEDIndex):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return ERPSED

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
    

class BOPIndex(DocumentIndex):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return BOP

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
    

class SSRIndex(DocumentIndex):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return SSR

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
    
class PredictionIndex(DocumentIndex):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Prediction

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()