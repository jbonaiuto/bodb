from django import forms
from django.forms.models import inlineformset_factory
from bodb.forms.document import DocumentForm
from bodb.models import Model, Prediction, SSR, PredictionSSR
from registration.models import User
from taggit.forms import TagField
from uscbp.forms import nested_formset_factory

class PredictionForm(DocumentForm):
    model = forms.ModelChoiceField(queryset=Model.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(widget=forms.HiddenInput, required=False)
    tags = TagField(required=False)

    class Meta:
        model = Prediction


class PredictionInlineForm(forms.ModelForm):
    model = forms.ModelChoiceField(queryset=Model.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'50','rows':'3'}),required=True)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Prediction
        exclude=('tags',)


class PredictionSSRInlineForm(forms.ModelForm):
    prediction = forms.ModelChoiceField(queryset=Prediction.objects.all(),widget=forms.HiddenInput,required=False)
    ssr = forms.ModelChoiceField(queryset=SSR.objects.all(),widget=forms.HiddenInput,required=False)
    ssr_collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    ssr_title = forms.CharField(widget=forms.TextInput(attrs={'size':'20'}),required=True)
    ssr_brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'50','rows':'3'}),required=True)
    ssr_draft=forms.CharField(widget=forms.HiddenInput,required=False)
    ssr_public = forms.BooleanField(widget=forms.HiddenInput, required=False)
    ssr_type=forms.CharField(widget=forms.HiddenInput,required=False)

    def __init__(self, *args, **kwargs):
        super(PredictionSSRInlineForm, self).__init__(*args, **kwargs)
        instance=kwargs.get('instance')
        if instance is not None and instance.ssr is not None:
            self.initial['ssr_collator']=instance.ssr.collator
            self.initial['ssr_title']=instance.ssr.title
            self.initial['ssr_brief_description']=instance.ssr.brief_description
            self.initial['ssr_draft']=instance.ssr.draft
            self.initial['ssr_public']=instance.ssr.public
            self.initial['ssr_type']=instance.ssr.type

    class Meta:
        model = PredictionSSR


PredictionFormSet = nested_formset_factory(Model,Prediction,PredictionSSR,form=PredictionInlineForm,
    nested_form=PredictionSSRInlineForm,fk_name='model',nested_fk_name='prediction',can_delete=True,
    nested_can_delete=True,extra=0,nested_extra=1,nested_max_num=1)


PredictionSSRFormSet = inlineformset_factory(Prediction,PredictionSSR,form=PredictionSSRInlineForm,fk_name='prediction',
    can_delete=True,extra=1,max_num=1)


class SSRForm(DocumentForm):
    type=forms.CharField(widget=forms.HiddenInput,required=False)

    class Meta:
        model=SSR