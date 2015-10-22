from django import forms
from django.forms.models import ErrorList, formset_factory, inlineformset_factory
from bodb.forms.document import DocumentWithLiteratureForm
from bodb.models import Literature, SED, BrainRegion, ConnectivitySED, ERPSED, ERPComponent, ElectrodePositionSystem, ElectrodePosition, ElectrodeCap, CoordinateSpace, BrainImagingSED, SEDCoord, Document, BuildSED, Model, TestSED, SSR
from registration.models import User
from taggit.forms import TagField
from uscbp.forms import nested_formset_factory

import datetime
from django.forms.extras.widgets import SelectDateWidget
from django.forms import ModelForm, Form

from functools import partial
DateInput = partial(forms.DateInput, {'class': 'datepicker'}) 

class SEDForm(DocumentWithLiteratureForm):
    type=forms.CharField(widget=forms.HiddenInput,required=False)

    class Meta:
        model=SED


class ConnectivitySEDForm(SEDForm):
    source_region = forms.ModelChoiceField(queryset=BrainRegion.objects.all(), widget=forms.HiddenInput, required=True)
    target_region = forms.ModelChoiceField(queryset=BrainRegion.objects.all(), widget=forms.HiddenInput, required=True)

    class Meta:
        model=ConnectivitySED


class ERPSEDForm(SEDForm):
    cognitive_paradigm = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}), required=False)
    sensory_modality = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}), required=False)
    response_modality = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}), required=False)
    control_condition = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    experimental_condition = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)

    class Meta:
        model=ERPSED


class ERPComponentInlineForm(forms.ModelForm):
    erp_sed = forms.ModelChoiceField(queryset=ERPSED.objects.all(),widget=forms.HiddenInput,required=False)
    component_name=forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    latency_peak=forms.DecimalField(widget=forms.TextInput(attrs={'size':'10'}), required=False)
    latency_peak_type=forms.ChoiceField(choices=ERPComponent.LATENCY_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=False)
    latency_onset=forms.DecimalField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    amplitude_peak=forms.DecimalField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    amplitude_mean=forms.DecimalField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    electrode_position_system=forms.ModelChoiceField(ElectrodePositionSystem.objects.all(),
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif', 'onchange': 'updateElectrodePosition(this.id, this.value)'}),
        required=False)
    electrode_position=forms.ModelChoiceField(ElectrodePosition.objects.all(),
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=False)
    electrode_cap=forms.ModelChoiceField(ElectrodeCap.objects.all(),
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=False)
    channel_number=forms.CharField(widget=forms.TextInput(attrs={'size':'5'}),required=False)
    source=forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    interpretation=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=False)

    class Meta:
        model=ERPComponent


ERPComponentFormSet = inlineformset_factory(ERPSED, ERPComponent, form=ERPComponentInlineForm, fk_name='erp_sed',
    extra=0, can_delete=True)


class BrainImagingSEDForm(SEDForm):
    control_condition = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    experimental_condition = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    method = forms.ChoiceField(choices=BrainImagingSED.METHOD_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif', 'onchange': 'updateColumns()'}),
        required=False)
    coord_space = forms.ModelChoiceField(CoordinateSpace.objects.all(), required=False)
    core_header_1 = forms.ChoiceField(choices=BrainImagingSED.HEADER_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif', 'onchange': 'updateColumns()'}),
        required=True)
    core_header_2 = forms.ChoiceField(choices=BrainImagingSED.HEADER_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif', 'onchange': 'updateColumns()'}),
        required=True)
    core_header_3 = forms.ChoiceField(choices=BrainImagingSED.HEADER_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif', 'onchange': 'updateColumns()'}),
        required=True)
    core_header_4 = forms.ChoiceField(choices=BrainImagingSED.HEADER_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif', 'onchange': 'updateColumns()'}),
        required=True)
    extra_header = forms.CharField(widget=forms.TextInput(attrs={'size':'50', 'onkeyup': 'updateExtraHeader(this.value)'}),
        required=False)
    data = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'10'}),required=False)

    class Meta:
        model=BrainImagingSED


class SEDCoordCleanForm(forms.Form):
    sed_coord_id=forms.CharField(widget=forms.HiddenInput,required=True)
    coord_space = forms.ModelChoiceField(CoordinateSpace.objects.all(), widget=forms.HiddenInput, required=False)
    brain_region_error=forms.CharField(widget=forms.HiddenInput,required=False)
    brain_region_options=forms.ChoiceField(choices=(('name','Match region by name'),('coordinate','Match region by coordinate')),
        widget=forms.RadioSelect,required=False)
    brain_region_change_name=forms.ModelChoiceField(queryset=BrainRegion.objects.none(),
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}),
        required=False)
    brain_region_change_coord=forms.ModelChoiceField(queryset=BrainRegion.objects.none(),
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}),
        required=False)
    hemisphere_error=forms.CharField(widget=forms.HiddenInput,required=True)
    hemisphere_options=forms.ChoiceField(choices=(('hemisphere','Update hemisphere'),('coordinate','Update coordinate')),
        widget=forms.RadioSelect,required=False)
    def __init__(self, user=None, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False):
        self.coord=SEDCoord.objects.get(id=initial['sed_coord_id'])
        coord_space=initial['coord_space']
        self.base_fields['brain_region_change_coord'].queryset=BrainRegion.objects.filter(brainregionvolume__coord_space=coord_space,
            brainregionvolume__coords__x=self.coord.coord.x,
            brainregionvolume__coords__y=self.coord.coord.y,
            brainregionvolume__coords__z=self.coord.coord.z)
        self.base_fields['brain_region_change_name'].queryset=BrainRegion.objects.filter(brainregionvolume__coord_space=coord_space)
        if initial['hemisphere_error']=='1':
            self.hemiErr=True
        else:
            self.hemiErr=False
        super(SEDCoordCleanForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix,
            empty_permitted)


SEDCoordCleanFormSet=formset_factory(SEDCoordCleanForm, extra=0, can_delete=False)


class BuildSEDInlineForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    sed = forms.ModelChoiceField(queryset=SED.objects.all(),widget=forms.HiddenInput,required=False)
    relationship = forms.ChoiceField(choices=BuildSED.RELATIONSHIP_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=True)
    relevance_narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'37','rows':'3'}),required=False)

    class Meta:
        model=BuildSED


BuildSEDFormSet = lambda *a, **kw: inlineformset_factory(Document,BuildSED,form=BuildSEDInlineForm, fk_name='document',
    extra=kw.pop('extra', 0), can_delete=True)(*a, **kw)


class TestSEDInlineForm(forms.ModelForm):
    model = forms.ModelChoiceField(queryset=Model.objects.all(),widget=forms.HiddenInput,required=False)
    sed = forms.ModelChoiceField(queryset=SED.objects.all(),widget=forms.HiddenInput,required=False)
    ssr = forms.ModelChoiceField(queryset=SSR.objects.all(),widget=forms.HiddenInput,required=False)
    relationship = forms.ChoiceField(choices=TestSED.RELATIONSHIP_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=True)
    relevance_narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'37','rows':'3'}),required=False)

    class Meta:
        model=TestSED


TestSEDFormSet = lambda *a, **kw: inlineformset_factory(Model,TestSED,form=TestSEDInlineForm, fk_name='model',
    extra=kw.pop('extra', 0), can_delete=True)(*a, **kw)


class SEDReportForm(Form):
    format=forms.ChoiceField(choices=[('rtf','RTF'),('pdf','PDF')],required=True, help_text='File format to export')
    figure_display=forms.BooleanField(required=False, help_text='Display figures in report')
    narrative_display=forms.BooleanField(required=False, help_text='Display narrative in report')
    related_model_display=forms.BooleanField(required=False, help_text='Display related models in report')
    related_bop_display=forms.BooleanField(required=False, help_text='Display related BOPs in report')
    related_brainregion_display=forms.BooleanField(required=False, help_text='Display related brain regions in report')
    reference_display=forms.BooleanField(required=False, help_text='Display references in report')

