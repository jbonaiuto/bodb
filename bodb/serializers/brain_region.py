from django.forms import widgets
from rest_framework import serializers
from bodb.models import BrainRegion, RelatedBrainRegion, CoordinateSpace, ThreeDCoord, ElectrodePosition, ElectrodePositionSystem
        
        
class BrainRegionSerializer(serializers.ModelSerializer):
     
    class Meta:
        model = BrainRegion
        fields = ('id', 'name', 'brain_region_type', 'nomenclature')
                
        
class RelatedBrainRegionSerializer(serializers.ModelSerializer):
    brain_region = BrainRegionSerializer()
    
    class Meta:
        model = RelatedBrainRegion
        fields = ('brain_region', 'relationship',)
        
        
class ThreeDCoordSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ThreeDCoord
        fields = ('id','x','y','z')
        
        
class CoordinateSpaceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CoordinateSpace
        fields = ('id','name')
        
        
class ElectrodePositionSystemSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ElectrodePositionSystem
        fields = ('id','name')
      
 
class ElectrodePositionSerializer(serializers.ModelSerializer):
    
    position_system = ElectrodePositionSystemSerializer()
    
    class Meta:
        model = ElectrodePosition
        fields = ('id','name', 'position_system')