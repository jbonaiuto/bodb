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

from django.contrib.auth import authenticate, login, logout
from tastypie.http import HttpUnauthorized, HttpForbidden

from haystack.query import SearchQuerySet, EmptySearchQuerySet

class SearchResourceMixin:
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/search/?$" % (self._meta.resource_name), self.wrap_view('get_search'), name="api_get_search"),
            ]

    def get_search(self, request, **kwargs):
        '''
        Custom endpoint for search
        '''

        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        query = request.GET.get('q', '')

        results = SearchQuerySet().models(self._meta.queryset.model).auto_query(query)
        if not results:
            results = EmptySearchQuerySet()

        paginator = Paginator(request.GET, results, resource_uri='/bodb/api/v1/%s/search/' % self._meta.resource_name)

        bundles = []
        for result in paginator.page()['objects']:
            bundle = self.build_bundle(obj=result.object, request=request)
            bundles.append(self.full_dehydrate(bundle))

        object_list = {
            'meta': paginator.page()['meta'],
            'objects': bundles
        }
        object_list['meta']['search_query'] = query

        self.log_throttled_access(request)
        return self.create_response(request, object_list)
    

class DocumentResource(SearchResourceMixin, ModelResource):
    
    collator = fields.ToOneField('bodb.api.UserResource','collator')
    last_modified_by = fields.ToOneField('bodb.api.UserResource','last_modified_by')
    
    class Meta:
        queryset = Document.objects.all()
        resource_name = 'document'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
    def hydrate_collator(self, bundle):
        bundle.data['collator'] = bundle.request.user
        return bundle
    
    def hydrate_last_modified_by(self, bundle):
        bundle.data['last_modified_by'] = bundle.request.user
        return bundle
    

class BuildSEDResource(ModelResource):
    build_sed = fields.ForeignKey('bodb.api.SEDResource', 'sed', full = True, null=True) 
    
    class Meta:
        queryset = BuildSED.objects.all()
        resource_name = 'build_sed'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class TestSEDResource(ModelResource):
    test_sed = fields.ForeignKey('bodb.api.SEDResource', 'sed', full = True, null=True) 
    
    class Meta:
        queryset = TestSED.objects.all()
        resource_name = 'test_sed'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)

class SEDResource(DocumentResource):
    related_brain_regions = fields.ToManyField('bodb.api.RelatedBrainRegionResource', 'related_region_document', full=True,  null=True)
    
    class Meta:
        #allowed_methods = ['get','post', 'put']
        queryset = SED.objects.all()
        resource_name = 'sed'
        authorization = BODBAPIAuthorization()
        #authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)

class BrainImaginingSEDResource(SEDResource):
    coordinates = fields.ToManyField('bodb.api.SEDCoordResource', 'coordinates', full=True,  null=True)

    class Meta:
        queryset = BrainImagingSED.objects.all()
        resource_name = 'brain_imagining_sed'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class SEDCoordResource(ModelResource):
    threedcoord = fields.ForeignKey('bodb.api.ThreeDCoordResource', 'threedcoord', full = True, null=True)

    class Meta:
        queryset = SEDCoord.objects.all()
        resource_name = 'sed_coord'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class ThreeDCoordResource(ModelResource):

    class Meta:
        queryset = ThreeDCoord.objects.all()
        resource_name = 'threedcoord'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class ERPSEDResource(SEDResource):
    erp_component = fields.ToManyField('bodb.api.ERPComponentResource', 'components', full=True,  null=True)
    
    class Meta:
        queryset = ERPSED.objects.all()
        resource_name = 'erp_sed'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class ERPComponentResource(ModelResource):

    class Meta:
        queryset = ERPComponent.objects.all()
        resource_name = 'erp_component'
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
    bop = fields.ForeignKey('bodb.api.BOPResource', 'bop', full=True, null=True)
    class Meta:
        queryset = RelatedBOP.objects.all()
        resource_name = 'related_bop'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)

class BOPResource(DocumentResource):
    related_bops = fields.ToManyField('bodb.api.RelatedBOPResource', 'related_bop_document', full=True, null=True)
    related_models = fields.ToManyField('bodb.api.RelatedModelResource', 'related_model_document', full=True, null=True)
    related_brain_regions = fields.ToManyField('bodb.api.RelatedBrainRegionResource', 'related_region_document', full=True,  null=True)
    
    class Meta:
        queryset = BOP.objects.all()
        resource_name = 'bop'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        

class SSRResource(DocumentResource):   
    class Meta:
        queryset = RelatedModel.objects.all()
        resource_name = 'ssr'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
    
class PredictionResource(DocumentResource):   
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
        resource_name = 'model'
        authorization = BODBAPIAuthorization()
        authentication = SessionAuthentication()
        cache = SimpleCache(timeout=10)
        
class BODBModelResource(DocumentResource):
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
        
class DocumentFigureResource(SearchResourceMixin, ModelResource):
    document = fields.ForeignKey('bodb.api.DocumentResource', 'document', full=True, null=True)
    
    class Meta:
        queryset = DocumentFigure.objects.all()
        resource_name = 'documentfigure'
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
        
        
class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        fields = ['first_name', 'last_name', 'email']
        allowed_methods = ['get', 'post']
        resource_name = 'user'

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/login%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('login'), name="api_login"),
            url(r'^(?P<resource_name>%s)/logout%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('logout'), name='api_logout'),
        ]

    def login(self, request, **kwargs):
        self.method_check(request, allowed=['post'])

        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))

        username = data.get('username', '')
        password = data.get('password', '')

        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return self.create_response(request, {
                    'success': True
                })
            else:
                return self.create_response(request, {
                    'success': False,
                    'reason': 'disabled',
                    }, HttpForbidden )
        else:
            return self.create_response(request, {
                'success': False,
                'reason': 'incorrect',
                }, HttpUnauthorized )

    def logout(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        if request.user and request.user.is_authenticated():
            logout(request)
            return self.create_response(request, { 'success': True })
        else:
            return self.create_response(request, { 'success': False }, HttpUnauthorized)
        
