from django import forms
from django.forms import Form
from django.forms.models import inlineformset_factory
from bodb.forms.document import DocumentWithLiteratureForm
from bodb.models import BOP, Document, RelatedBOP

class BOPForm(DocumentWithLiteratureForm):
    parent = forms.ModelChoiceField(queryset=BOP.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model=BOP


class RelatedBOPInlineForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    relevance_narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'40','rows':'3'}),required=False)
    bop = forms.ModelChoiceField(queryset=BOP.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model=RelatedBOP


RelatedBOPFormSet = lambda *a, **kw: inlineformset_factory(Document,RelatedBOP,form=RelatedBOPInlineForm, fk_name='document',
    extra=kw.pop('extra', 0), can_delete=True)(*a, **kw)


class BOPRelatedBOPInlineForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    relationship = forms.ChoiceField(choices=RelatedBOP.RELATIONSHIP_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=True)
    relevance_narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'40','rows':'3'}),required=False)
    bop = forms.ModelChoiceField(queryset=BOP.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model=RelatedBOP


BOPRelatedBOPFormSet = inlineformset_factory(Document,RelatedBOP,form=BOPRelatedBOPInlineForm,fk_name='document',extra=0,
    can_delete=True)

class BOPReportForm(Form):
    format=forms.ChoiceField(choices=[('rtf','RTF'),('pdf','PDF')],required=True, help_text='File format to export')
    figure_display=forms.BooleanField(required=False, help_text='Display figures in report')
    narrative_display=forms.BooleanField(required=False, help_text='Display narrative in report')
    childbop_display=forms.BooleanField(required=False, help_text='Display child BOPs in report')
    summary_display=forms.BooleanField(required=False, help_text='Display SEDs, SSRs and Predictions in report')
    related_model_display=forms.BooleanField(required=False, help_text='Display related models in report')
    related_bop_display=forms.BooleanField(required=False, help_text='Display related BOPs in report')
    related_brainregion_display=forms.BooleanField(required=False, help_text='Display related brain regions in report')
    reference_display=forms.BooleanField(required=False, help_text='Display references in report')
    include_seds=forms.BooleanField(required=False, help_text='Include SED reports in report')