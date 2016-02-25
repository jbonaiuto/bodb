from tastypie.resources import ModelResource
from bodb.models import SED, BOP, Model, SSR, BrainRegion, RelatedModel, RelatedBOP, RelatedBrainRegion
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


class SEDResource(ModelResource):
    
    class Meta:
        queryset = SED.objects.all()
        resource_name = 'sed'
        #authorization = DjangoAuthorization()
        #authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class RelatedBOPResource(ModelResource):   
    bop = fields.ForeignKey('bodb.api.BOPResource', 'related_bop', full=True, null=True)
    class Meta:
        queryset = RelatedBOP.objects.all()
        resource_name = 'related_bop'
        #authorization = DjangoAuthorization()
        #authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)

class BOPResource(ModelResource):
    
    class Meta:
        queryset = BOP.objects.all()
        resource_name = 'bop'
        #authorization = DjangoAuthorization()
        #authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        

class RelatedModelResource(ModelResource):   
    class Meta:
        queryset = RelatedModel.objects.all()
        resource_name = 'related_model'
        #authorization = DjangoAuthorization()
        #authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
    
        
class ModelResource(ModelResource):
    related_models = fields.ToManyField('bodb.api.RelatedModelResource', 'related_model_document', full=True, null=True)
    related_bops = fields.ToManyField('bodb.api.RelatedBOPResource', 'related_bop_document', full=True, null=True)
    related_brain_regions = fields.ToManyField('bodb.api.RelatedBrainRegionResource', 'related_region_document', null=True)
    
    class Meta:
        queryset = Model.objects.all()
        resource_name = 'model'
        #authorization = DjangoAuthorization()
        #authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class SSRResource(ModelResource):
    class Meta:
        queryset = SSR.objects.all()
        resource_name = 'ssr'
        #authorization = DjangoAuthorization()
        #authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class BrainRegionResource(ModelResource):
    class Meta:
        queryset = BrainRegion.objects.all()
        resource_name = 'brain_region'
        #authorization = DjangoAuthorization()
        #authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class RelatedBrainRegionResource(ModelResource):  
    bop = fields.ToManyField(BrainRegionResource, 'brain_region', full=True, null=True) 
    class Meta:
        queryset = RelatedBrainRegion.objects.all()
        resource_name = 'related_brain_region'
        #authorization = DjangoAuthorization()
        #authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
