from tastypie.resources import ModelResource
from bodb.models import *
from django.contrib.auth.models import User
from tastypie import fields
from tastypie.authentication import SessionAuthentication
from tastypie.cache import SimpleCache
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from tastypie.paginator import Paginator
from django.conf.urls import patterns, url
from tastypie.utils import trailing_slash 
from bodb.authorization import BODBAPIAuthorization

class BuildSEDResource(ModelResource):
    build_sed = fields.ForeignKey('bodb.api.SEDResource', 'build_sed', full = True, null=True) 
    
    class Meta:
        queryset = BuildSED.objects.all()
        resource_name = 'build_sed'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class TestSEDResource(ModelResource):
    test_sed = fields.ForeignKey('bodb.api.SEDResource', 'test_sed', full = True, null=True) 
    
    class Meta:
        queryset = TestSED.objects.all()
        resource_name = 'test_sed'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)

class SEDResource(ModelResource):
    related_brain_regions = fields.ToManyField('bodb.api.RelatedBrainRegionResource', 'related_region_document', full=True,  null=True)
    
    class Meta:
        queryset = SED.objects.all()
        resource_name = 'sed'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)

class BrainImaginingSEDResource(SEDResource):

    class Meta:
        queryset = BrainImagingSED.objects.all()
        resource_name = 'brain_imagining_sed'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class ERPSEDResource(SEDResource):

    class Meta:
        queryset = ERPSED.objects.all()
        resource_name = 'erp_sed'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class ConnectivitySEDResource(SEDResource):
    source_region = fields.ForeignKey('bodb.api.BrainRegionResource', 'source_region', full=True, null=True)
    target_region = fields.ForeignKey('bodb.api.BrainRegionResource', 'target_region', full=True, null=True)

    class Meta:
        queryset = ConnectivitySED.objects.all()
        resource_name = 'connectivity_sed'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class RelatedBOPResource(ModelResource):   
    bop = fields.ForeignKey('bodb.api.BOPResource', 'related_bop', full=True, null=True)
    class Meta:
        queryset = RelatedBOP.objects.all()
        resource_name = 'related_bop'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)

class BOPResource(ModelResource):
    related_bops = fields.ToManyField('bodb.api.RelatedBOPResource', 'related_bop_document', full=True, null=True)
    related_models = fields.ToManyField('bodb.api.RelatedModelResource', 'related_model_document', full=True, null=True)
    related_brain_regions = fields.ToManyField('bodb.api.RelatedBrainRegionResource', 'related_region_document', full=True,  null=True)
    
    class Meta:
        queryset = BOP.objects.all()
        resource_name = 'bop'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        

class SSRResource(ModelResource):   
    class Meta:
        queryset = RelatedModel.objects.all()
        resource_name = 'ssr'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
    
class PredictionResource(ModelResource):   
    ssr = fields.ForeignKey('bodb.api.SSRResource', 'ssr', full = True, null=True) 
    
    class Meta:
        queryset = Prediction.objects.all()
        resource_name = 'prediction'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class RelatedModelResource(ModelResource):   
    class Meta:
        queryset = RelatedModel.objects.all()
        resource_name = 'related_model'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class BODBModelResource(ModelResource):
    build_seds = fields.ToManyField('bodb.api.BuildSEDResource', 'related_build_sed_document', full=True, null=True)
    test_seds = fields.ToManyField('bodb.api.TestSEDResource', 'related_test_sed_document', full=True, null=True)
    predictions = fields.ToManyField('bodb.api.PredictionResource', 'prediction', full=True, null=True)
    related_bops = fields.ToManyField('bodb.api.RelatedBOPResource', 'related_bop_document', full=True, null=True)
    related_models = fields.ToManyField('bodb.api.RelatedModelResource', 'related_model_document', full=True, null=True)
    related_brain_regions = fields.ToManyField('bodb.api.RelatedBrainRegionResource', 'related_region_document', full=True,  null=True)
    
    class Meta:
        queryset = Model.objects.all()
        resource_name = 'model'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
        
class BrainRegionResource(ModelResource):
    class Meta:
        queryset = BrainRegion.objects.all()
        resource_name = 'brain_region'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class RelatedBrainRegionResource(ModelResource):  
    brain_region = fields.ForeignKey('bodb.api.BrainRegionResource', 'brain_region', full = True, null=True) 
    class Meta:
        queryset = RelatedBrainRegion.objects.all()
        resource_name = 'related_brain_region'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
