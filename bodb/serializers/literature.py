from django.forms import widgets
from rest_framework import serializers
from bodb.models import Literature, LiteratureAuthor, Author
from bodb.serializers.user import UserSerializer

class AuthorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Author
        fields = ('id', 'first_name', 'last_name')

class LiteratureAuthorSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    
    class Meta:
        model = LiteratureAuthor
        fields = ('author', 'order')

        
class LiteratureSerializer(serializers.ModelSerializer):
    authors = LiteratureAuthorSerializer()
    collator = UserSerializer()
    
    class Meta:
        model = Literature
        fields = ('id', 'title','collator', 'authors')
        
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(LiteratureSerializer, self).__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)