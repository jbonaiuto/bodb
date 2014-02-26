from django.forms import widgets
from rest_framework import serializers
from bodb.models import BOP

class BOPSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = BOP
