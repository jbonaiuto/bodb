from rest_framework import serializers
from bodb.models import SSR, Prediction
from bodb.serializers.user import UserSerializer
from bodb.serializers.document import DocumentFigureSerializer, DocumentTagSerializer

class SSRSerializer(serializers.ModelSerializer):
    collator = UserSerializer()
    last_modified_by = UserSerializer()
    figures = DocumentFigureSerializer()
    tags=DocumentTagSerializer()
    
    class Meta:
        model = SSR
        fields = ('id', 'title', 'collator', 'last_modified_by', 'last_modified_time', 
                  'brief_description','type','narrative','tags', 'public','figures')
        
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(SSRSerializer, self).__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class PredictionSerializer(serializers.ModelSerializer):
    collator = UserSerializer()
    last_modified_by = UserSerializer()
    ssr = SSRSerializer(source = 'get_ssr', fields = ('id','title','brief_description','type'))
    tags=DocumentTagSerializer()
    
    class Meta:
        model = Prediction
        fields = ('id', 'title','collator','last_modified_by','last_modified_time','brief_description', 'tags','public','ssr')