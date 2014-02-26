from django.forms import widgets
from rest_framework import serializers
from bodb.models import SSR

class SSRSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SSR
