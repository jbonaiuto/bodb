from django.forms import widgets
from rest_framework import serializers
from bodb.models import Document, DocumentFigure

class DocumentFigureSerializer(serializers.ModelSerializer):
    
    link = serializers.Field('get_absolute_url')

    class Meta:
        model = DocumentFigure
        fields = ('title', 'caption', 'order', 'link')

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document