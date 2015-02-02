from django import forms
from django.forms.models import inlineformset_factory
from bodb.models import Document, DocumentFigure, Literature
from registration.models import User
from taggit.forms import TagField
from uscbp.widgets import ImageWidget

class DocumentForm(forms.ModelForm):
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(help_text='Make the entry public', required=False)
    tags = TagField(required=False)

    def clean(self):
        if self.data['draft']!='1':
            return super(DocumentForm, self).clean()
        else:
            self._errors.clear()
        return self.cleaned_data


class DocumentWithLiteratureForm(DocumentForm):
    literature = forms.ModelMultipleChoiceField(queryset=Literature.objects.order_by('title'),
        widget=forms.MultipleHiddenInput, required=False)


class DocumentFigureForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    figure=forms.ImageField(required=True, max_length=500, widget=ImageWidget)
    title=forms.CharField(widget=forms.TextInput(attrs={'size':'20'}),required=True)
    caption=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=False)
    order=forms.IntegerField(widget=forms.TextInput(attrs={'size':'3'}),required=True)

    class Meta:
        model=DocumentFigure

DocumentFigureFormSet = inlineformset_factory(Document, DocumentFigure, form=DocumentFigureForm, fk_name='document',
    extra=0, can_delete=True, can_order=True)