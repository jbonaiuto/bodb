from django import forms
from django.forms.models import inlineformset_factory
from bodb.forms.document import DocumentWithLiteratureForm
from bodb.models import BOP, Document, RelatedBOP

class BOPForm(DocumentWithLiteratureForm):
    parent = forms.ModelChoiceField(queryset=BOP.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model=BOP


class RelatedBOPInlineForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    relevance_narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'40','rows':'3'}),required=True)
    bop = forms.ModelChoiceField(queryset=BOP.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model=RelatedBOP


RelatedBOPFormSet = inlineformset_factory(Document,RelatedBOP,form=RelatedBOPInlineForm,fk_name='document',extra=0,
    can_delete=True)


class BOPRelatedBOPInlineForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    relationship = forms.ChoiceField(choices=RelatedBOP.RELATIONSHIP_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=True)
    relevance_narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'40','rows':'3'}),required=True)
    bop = forms.ModelChoiceField(queryset=BOP.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model=RelatedBOP


BOPRelatedBOPFormSet = inlineformset_factory(Document,RelatedBOP,form=BOPRelatedBOPInlineForm,fk_name='document',extra=0,
    can_delete=True)
