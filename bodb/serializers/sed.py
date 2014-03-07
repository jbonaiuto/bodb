from django.forms import widgets
from rest_framework import serializers
from bodb.models import SED, ERPSED, BrainImagingSED, ConnectivitySED
from bodb.serializers.brain_region import RelatedBrainRegionSerializer
from bodb.serializers.literature import LiteratureSerializer

class SEDSerializer(serializers.ModelSerializer):
    literature = LiteratureSerializer()
    brain_region = RelatedBrainRegionSerializer()
    
    class Meta:
        model = SED
        #depth = 1

class ERPSEDSerializer(SEDSerializer):
    
    class Meta:
        model = ERPSED
        
class BrainImagingSEDSerializer(SEDSerializer):
    
    class Meta:
        model = BrainImagingSED
        
class ConnectivitySEDSerializer(SEDSerializer):
    
    class Meta:
        model = ConnectivitySED