from django.forms import widgets
from rest_framework import serializers
from bodb.models import Module, Model, RelatedModel, ModelAuthor, Author, Variable
from bodb.serializers.brain_region import RelatedBrainRegionSerializer
from bodb.serializers.literature import LiteratureSerializer
from bodb.serializers.bop import RelatedBOPSerializer
from bodb.serializers.sed import SEDSerializer, BuildSEDSerializer, TestSEDSerializer
from bodb.serializers.user import UserSerializer


class AuthorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Author
        fields = ('id', 'first_name', 'last_name')

class ModelAuthorSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    
    class Meta:
        model = ModelAuthor
        fields = ('author', 'order')

class ModelSimpleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Model
        fields =  ('id', 'title','brief_description',)


class RelatedModelSerializer(serializers.ModelSerializer):
    related_model = ModelSimpleSerializer(source = 'model')
    
    class Meta:
        model = RelatedModel
        fields = ('related_model', 'relationship',)
        
        
class VariableSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Variable
        fields = ('id', 'var_type', 'data_type', 'name', 'description') 
        
        
class SubmoduleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Module
        fields = ('id', 'title','brief_description') 


#need to add Architecture and SSR
class ModelSerializer(serializers.ModelSerializer):
    references = LiteratureSerializer(source = 'literature', fields = ('id','title','authors','collator'))
    variables = VariableSerializer(source = 'related_module')
    submodules = SubmoduleSerializer(source = 'children')
    related_brain_region = RelatedBrainRegionSerializer(source = 'related_region_document')
    related_bop = RelatedBOPSerializer(source = 'related_bop_document')
    build_sed = BuildSEDSerializer(source = 'related_build_sed_document')
    test_sed = TestSEDSerializer(source = 'related_test_sed_document')
    related_model = RelatedModelSerializer(source = 'related_model_document')
    authors = ModelAuthorSerializer()
    collator = UserSerializer()
    last_modified_by = UserSerializer()
    
    
    class Meta:
        model = Model
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 
                  'authors', 'brief_description', 'narrative', 'tags','public','figures','variables', 'submodules', 'build_sed','test_sed',
                  'modeldb_accession_number', 'execution_url','documentation_url','description_url','simulation_url', 
                  'related_model','related_bop','related_brain_region','references')


