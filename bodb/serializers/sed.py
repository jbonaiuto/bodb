from django.forms import widgets
from rest_framework import serializers
from bodb.models import SED, ERPSED, BrainImagingSED, ConnectivitySED, BuildSED, TestSED
from bodb.serializers.brain_region import BrainRegionSerializer, RelatedBrainRegionSerializer
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
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 
                  'brief_description','narrative','tags', 'public',
                  'cognitive_paradigm','sensory_modality', 'response_modality','control_condition', 'experimental_condition',
                  'figures','related_bop','related_brain_region', 'references')
        
        
class BrainImagingSEDSerializer(SEDSerializer):
    
    class Meta:
        model = BrainImagingSED
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 
                  'brief_description','narrative','tags', 'public',
                  'method','control_condition','experimental_condition','coord_space',
                  'core_header_1', 'core_header_2', 'core_header_3', 'core_header_4','extra_header',
                  'figures','related_bop','related_brain_region', 'references')
        
        
        
class ConnectivitySEDSerializer(SEDSerializer):
    source_region = BrainRegionSerializer(source = 'source_region')
    target_region = BrainRegionSerializer(source = 'target_region')
    
    class Meta:
        model = ConnectivitySED
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 
                  'source_region', 'target_region',
                  'brief_description','narrative','tags', 'public','figures','related_bop','related_brain_region', 'references')