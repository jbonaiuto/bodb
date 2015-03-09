from django import forms
from django.forms import Form
from django.forms.models import inlineformset_factory
from bodb.forms.document import DocumentForm
from bodb.models import Model, Prediction, SSR
from registration.models import User
from taggit.forms import TagField
from uscbp.forms import nested_formset_factory

class PredictionForm(DocumentForm):
    model = forms.ModelChoiceField(queryset=Model.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    ssr = forms.ModelChoiceField(queryset=SSR.objects.all(),widget=forms.HiddenInput,required=False)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(widget=forms.HiddenInput, required=False)
    tags = TagField(required=False)

    class Meta:
        model = Prediction


class PredictionInlineForm(forms.ModelForm):
    model = forms.ModelChoiceField(queryset=Model.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'50','rows':'3'}),required=False)
    ssr = forms.ModelChoiceField(queryset=SSR.objects.all(),widget=forms.HiddenInput,required=False)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Prediction
        exclude=('tags',)


PredictionFormSet = lambda *a, **kw: inlineformset_factory(Model,Prediction,form=PredictionInlineForm, fk_name='model',
    extra=kw.pop('extra', 0), can_delete=True)(*a, **kw)


class SSRForm(DocumentForm):
    type=forms.CharField(widget=forms.HiddenInput,required=False)

    class Meta:
        model=SSR


class SSRReportForm(Form):
    format=forms.ChoiceField(choices=[('rtf','RTF'),('pdf','PDF')],required=True, help_text='File format to export')
    figure_display=forms.BooleanField(required=False, help_text='Display figures in report')
    narrative_display=forms.BooleanField(required=False, help_text='Display narrative in report')
