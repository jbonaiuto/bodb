from django import forms
from bodb.models import Forum, Post
from registration.models import User

class PostForm(forms.ModelForm):
    forum = forms.ModelChoiceField(queryset=Forum.objects.all(),widget=forms.HiddenInput,required=False)
    parent = forms.ModelChoiceField(queryset=Post.objects.all(),widget=forms.HiddenInput,required=False)
    author = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    body = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)
    class Meta:
        model=Post