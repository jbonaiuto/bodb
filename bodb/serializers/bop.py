from django.forms import widgets
from rest_framework import serializers
from bodb.models import BOP, RelatedBOP
from bodb.serializers.brain_region import RelatedBrainRegionSerializer
from bodb.serializers.literature import LiteratureSerializer
#from bodb.serializers.model import RelatedModelSerializer

class BOPSerializer(serializers.ModelSerializer):
    references = LiteratureSerializer(source = 'literature', fields = ('id','title','authors','collator'))
    related_brain_region = RelatedBrainRegionSerializer(source = 'related_region_document')
    #related_model = RelatedModelSerializer(source = 'related_model_document')
    
    class Meta:
        model = BOP
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time',
                  'brief_description','narrative','tags', 'public','figures', 'related_bop',
        #'related_model',
        'related_brain_region', 'references')
        
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(BOPSerializer, self).__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class RelatedBOPSerializer(serializers.ModelSerializer):
    bop = BOPSerializer(fields = ('id','title', 'brief_description',))
    
    class Meta:
        model = RelatedBOP
        fields = ('bop', 'relationship','relevance_narrative')
        
#BOPSerializer.related_bop = RelatedBOPSerializer(source = 'related_bop_document')

