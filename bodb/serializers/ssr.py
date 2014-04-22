from django.forms import widgets
from rest_framework import serializers
from bodb.models import SSR

class SSRSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SSR
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 
                  'brief_description','narrative','tags', 'public','figures')
