from django.forms import widgets
from rest_framework import serializers
from bodb.models import SED, ERPSED, BrainImagingSED, ConnectivitySED, BuildSED, TestSED, SEDCoord, ERPComponent, ElectrodeCap
from bodb.serializers.brain_region import BrainRegionSerializer, RelatedBrainRegionSerializer, CoordinateSpaceSerializer, ThreeDCoordSerializer
from bodb.serializers.literature import LiteratureSerializer
from bodb.serializers.user import UserSerializer
from bodb.serializers.ssr import SSRSerializer
from bodb.serializers.document import DocumentFigureSerializer


class SEDSerializer(serializers.ModelSerializer):
    references = LiteratureSerializer(source = 'literature', fields = ('id','title','authors','collator'))
    related_brain_region = RelatedBrainRegionSerializer(source = 'related_region_document')
    collator = UserSerializer()
    last_modified_by = UserSerializer()
    figures = DocumentFigureSerializer()
    
    class Meta:
        model = SED
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 'type',
                  'brief_description','narrative','tags', 'public','figures','related_brain_region', 'references')
        
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
    sed = SEDSerializer(fields = ('id','title', 'type','brief_description',))
    
    class Meta:
        model = BuildSED
        fields = ('sed', 'relationship', 'relevance_narrative')
   
    
class TestSEDSerializer(serializers.ModelSerializer):
    sed = SEDSerializer(fields = ('id','title', 'type', 'brief_description',))
    ssr = SSRSerializer(source = 'get_ssr', fields = ('id','title', 'brief_description',))
    
    class Meta:
        model = TestSED
        fields = ('sed', 'ssr','relationship', 'relevance_narrative')


class ElectrodeCapSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ElectrodeCap
        fields = ('id', 'manufacturer','name','version','num_channels', 'image_filename')
    
    
class ERPComponentSerializer(serializers.ModelSerializer):

    electrode_cap = ElectrodeCapSerializer()
    
    class Meta:
        model = ERPComponent
        fields = ('id', 'component_name', 'latency_peak', 'latency_peak_type', 'latency_onset', 'amplitude_peak', 'amplitude_mean',
                  'electrode_position',
                  'electrode_cap', 'channel_number', 'source', 'interpretation')


class ERPSEDSerializer(SEDSerializer):
    
    erp_components = ERPComponentSerializer(source = 'components')
    figures = DocumentFigureSerializer()
    
    class Meta:
        model = ERPSED
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 'type',
                  'brief_description','narrative','tags', 'public',
                  'cognitive_paradigm','sensory_modality', 'response_modality','control_condition', 'experimental_condition',
                  'erp_components',
                  'figures','related_brain_region', 'references')
        
class SEDCoordSerializer(serializers.ModelSerializer):
    
    coord = ThreeDCoordSerializer()
    
    class Meta:
        model = SEDCoord
        fields = ('id','named_brain_region', 'hemisphere','coord','rcbf','statistic')
        
          
class BrainImagingSEDSerializer(SEDSerializer):
    
    coord_space = CoordinateSpaceSerializer()
    coordinates = SEDCoordSerializer(source = 'coordinates')
    figures = DocumentFigureSerializer()
    
    class Meta:
        model = BrainImagingSED
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 'type',
                  'brief_description','narrative','tags', 'public',
                  'method','control_condition','experimental_condition','coord_space',
                  'core_header_1', 'core_header_2', 'core_header_3', 'core_header_4','extra_header','coordinates',
                  'figures','related_brain_region', 'references')
        
        
        
class ConnectivitySEDSerializer(SEDSerializer):
    source_region = BrainRegionSerializer(source = 'source_region')
    target_region = BrainRegionSerializer(source = 'target_region')
    figures = DocumentFigureSerializer()
    
    class Meta:
        model = ConnectivitySED
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 'type',
                  'source_region', 'target_region',
                  'brief_description','narrative','tags', 'public','figures','related_brain_region', 'references')