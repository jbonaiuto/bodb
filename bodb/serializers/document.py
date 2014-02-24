from django.forms import widgets
from rest_framework import serializers
from bodb.models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('collator', 'title', 'brief_description')