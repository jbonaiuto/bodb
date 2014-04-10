from django.forms import widgets
from rest_framework import serializers
from bodb.models import SED, ERPSED, BrainImagingSED, ConnectivitySED, BuildSED, TestSED
from bodb.serializers.brain_region import RelatedBrainRegionSerializer
from bodb.serializers.literature import LiteratureSerializer
from bodb.serializers.bop import RelatedBOPSerializer
from bodb.serializers.user import UserSerializer


class SEDSerializer(serializers.ModelSerializer):
    references = LiteratureSerializer(source = 'literature', fields = ('id','title','authors','collator'))
    related_brain_region = RelatedBrainRegionSerializer(source = 'related_region_document')
    related_bop = RelatedBOPSerializer(source = 'related_bop_document')
    #related_modeln = RelatedBrainRegionSerializer(source = 'document')
    collator = UserSerializer()
    last_modified_by = UserSerializer()
    
    class Meta:
        model = SED
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 
                  'brief_description','narrative','tags', 'public','figures','related_bop','related_brain_region', 'references')
        
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(SEDSerializer, self).__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
                
        
class BuildSEDSerializer(serializers.ModelSerializer):
    sed = SEDSerializer(fields = ('id','title', 'brief_description',))
    
    class Meta:
        model = BuildSED
        fields = ('sed', 'relationship', 'relevance_narrative')
        
    
class TestSEDSerializer(serializers.ModelSerializer):
    sed = SEDSerializer(fields = ('id','title', 'brief_description',))
    
    class Meta:
        model = TestSED
        fields = ('sed', 'relationship', 'relevance_narrative')

class ERPSEDSerializer(SEDSerializer):
    
    class Meta:
        model = ERPSED
        
class BrainImagingSEDSerializer(SEDSerializer):
    
    class Meta:
        model = BrainImagingSED
        
class ConnectivitySEDSerializer(SEDSerializer):
    
    class Meta:
        model = ConnectivitySED