from django.forms import widgets
from rest_framework import serializers
from bodb.models import SED, ERPSED, BrainImagingSED, ConnectivitySED

class SEDSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SED

class ERPSEDSerializer(SEDSerializer):
    
    class Meta:
        model = ERPSED
        
class BrainImagingSEDSerializer(SEDSerializer):
    
    class Meta:
        model = BrainImagingSED
        
class ConnectivitySEDSerializer(SEDSerializer):
    
    class Meta:
        model = ConnectivitySED