from django.forms import widgets
from rest_framework import serializers
from bodb.models import Literature

        
class LiteratureSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Literature