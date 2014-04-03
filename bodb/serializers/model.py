from django.forms import widgets
from rest_framework import serializers
from bodb.models import Model, RelatedModel
from bodb.serializers.brain_region import RelatedBrainRegionSerializer
from bodb.serializers.literature import LiteratureSerializer
from bodb.serializers.bop import RelatedBOPSerializer
from bodb.serializers.sed import SEDSerializer, BuildSEDSerializer, TestSEDSerializer

#need to add Architecture and SSR
class ModelSerializer(serializers.ModelSerializer):
    references = LiteratureSerializer(source = 'literature', fields = ('id','title','authors','collator'))
    related_brain_region = RelatedBrainRegionSerializer(source = 'related_region_document')
    related_bop = RelatedBOPSerializer(source = 'related_bop_document')
    build_sed = BuildSEDSerializer(source = 'related_build_sed_document')
    test_sed = TestSEDSerializer(source = 'related_test_sed_document')
    #related_model = RelatedModelSerializer(source = 'related_model_document')
    
    
    class Meta:
        model = Model
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 
                  'authors', 'brief_description', 'narrative', 'tags','public','build_sed','test_sed',
                  'modeldb_accession_number', 'execution_url','documentation_url','description_url','simulation_url', 
                  'related_model','related_bop','related_brain_region','references')

class RelatedModelSerializer(serializers.ModelSerializer):
    modelModel = ModelSerializer()
    
    class Meta:
        model = RelatedModel
        fields = ('modelModel', 'relationship',)

ModelSerializer.related_model = RelatedModelSerializer(source = 'related_model_document')

