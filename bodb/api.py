from tastypie.resources import ModelResource
from bodb.models import SED, BOP, Model, SSR, BrainRegion


class SEDResource(ModelResource):
    class Meta:
        queryset = SED.objects.all()
        resource_name = 'sed'

class BOPResource(ModelResource):
    class Meta:
        queryset = BOP.objects.all()
        resource_name = 'bop'
        
class ModelResource(ModelResource):
    class Meta:
        queryset = Model.objects.all()
        resource_name = 'model'
        
class SSRResource(ModelResource):
    class Meta:
        queryset = SSR.objects.all()
        resource_name = 'ssr'
        
class BrainRegionResource(ModelResource):
    class Meta:
        queryset = BrainRegion.objects.all()
        resource_name = 'brain_region'