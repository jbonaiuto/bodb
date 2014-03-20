from django import forms
from django.forms.models import inlineformset_factory
from bodb.models import BrainRegion, Nomenclature, Document, RelatedBrainRegion

class BrainRegionForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'size':'20'}),required=True)
    abbreviation = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    brain_region_type = forms.ChoiceField(choices=BrainRegion.REGION_TYPE_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}),
        required=True)
    parent_region = forms.ModelChoiceField(queryset=BrainRegion.objects.all(), required=False)
    nomenclature = forms.ModelChoiceField(queryset=Nomenclature.objects.all(), required=True)

    class Meta:
        model=BrainRegion


class RelatedBrainRegionInlineForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    relationship = forms.CharField(widget=forms.Textarea(attrs={'cols':'40','rows':'3'}),required=True)
    brain_region = forms.ModelChoiceField(queryset=BrainRegion.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model=RelatedBrainRegion


RelatedBrainRegionFormSet = inlineformset_factory(Document,RelatedBrainRegion,form=RelatedBrainRegionInlineForm,
    fk_name='document',extra=0, can_delete=True)
