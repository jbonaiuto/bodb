from django.forms import widgets
from rest_framework import serializers
from bodb.models import SED, ERPSED, BrainImagingSED, ConnectivitySED
from bodb.serializers.brain_region import RelatedBrainRegionSerializer
from bodb.serializers.literature import LiteratureSerializer

class SEDSerializer(serializers.ModelSerializer):
    references = LiteratureSerializer(source = 'literature', fields = ('id','title','authors','collator'))
    related_brain_region = RelatedBrainRegionSerializer(source = 'document')
    #related_modeln = RelatedBrainRegionSerializer(source = 'document')
    
    class Meta:
        model = SED
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 
                  'tags', 'brief_description', 'public','related_brain_region', 'references', 'forum')

class ERPSEDSerializer(SEDSerializer):
    
    class Meta:
        model = ERPSED
        
class BrainImagingSEDSerializer(SEDSerializer):
    
    class Meta:
        model = BrainImagingSED
        
class ConnectivitySEDSerializer(SEDSerializer):
    
    class Meta:
        model = ConnectivitySED