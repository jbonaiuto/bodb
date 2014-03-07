from django.forms import widgets
from rest_framework import serializers
from bodb.models import BrainRegion, RelatedBrainRegion
        
        
class BrainRegionSerializer(serializers.ModelSerializer):
     
    class Meta:
        model = BrainRegion
        
class RelatedBrainRegionSerializer(serializers.ModelSerializer):
    brain_region = BrainRegionSerializer()
    
    class Meta:
        model = RelatedBrainRegion