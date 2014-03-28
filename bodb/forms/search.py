from django import forms
from bodb.models import BrainRegion, Literature, SED
from taggit.forms import TagField

PUBLIC_CHOICES = (
    ('', ''),
    ('True', 'True'),
    ('False', 'False'),
)
SEARCH_CHOICES = (
    ('all', 'all'),
    ('any', 'any')
)

class SearchForm(forms.Form):
    keywords = forms.CharField(help_text="Keyword search", required=False)
    keywords_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    search_options = forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)


class DocumentSearchForm(SearchForm):
    public = forms.ChoiceField(choices=PUBLIC_CHOICES, help_text='Public entries', required=False)
    title = forms.CharField(help_text="Title", required=False)
    title_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    description = forms.CharField(help_text="Description", required=False)
    description_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    narrative = forms.CharField(help_text="Narrative", required=False)
    narrative_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    tags = TagField(required=False)
    tags_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    created_from = forms.DateTimeField(help_text="Earliest creation date", widget=forms.DateTimeInput, required=False)
    created_to = forms.DateTimeField(help_text="Latest creation date", widget=forms.DateTimeInput, required=False)
    collator = forms.BooleanField(help_text="Only search your entries", required=False)
    username = forms.CharField(help_text='Username of the collator',required=False)
    first_name = forms.CharField(help_text='First name of the collator',required=False)
    last_name = forms.CharField(help_text='Last name of the collator',required=False)
    related_brain_region = forms.CharField(help_text='Related brain region', required=False)
    related_brain_region_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    related_bop = forms.CharField(help_text="Related BOP", required=False)
    related_bop_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    related_model = forms.CharField(help_text="Related_Model", required=False)
    related_model_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)


class DocumentWithLiteratureSearchForm(DocumentSearchForm):
    related_literature_title = forms.CharField(help_text="Related literature title", required=False)
    related_literature_title_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    related_literature_author = forms.CharField(help_text="Related literature author", required=False)
    related_literature_author_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    related_literature_year_min = forms.CharField(help_text="Related literature min year", required=False)
    related_literature_year_max = forms.CharField(help_text="Related literature max year", required=False)
    related_literature_annotation = forms.CharField(help_text="Related literature annotation", required=False)
    related_literature_annotation_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)


class AllSearchForm(DocumentSearchForm):
    search_cocomac = forms.BooleanField(help_text='Search CoCoMac',required=False)
    search_brede = forms.BooleanField(help_text='Search Brede', required=False)


class UserSearchForm(SearchForm):
    username = forms.CharField(help_text='Username of the user',required=False)
    first_name = forms.CharField(help_text='First name of the user',required=False)
    last_name = forms.CharField(help_text='Last name of the user',required=False)
    bop = forms.CharField(help_text='BOPs entered by the user', required=False)
    bop_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    model = forms.CharField(help_text='Models entered by the user', required=False)
    model_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    sed = forms.CharField(help_text='SEDs entered by the user', required=False)
    sed_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    ssr = forms.CharField(help_text='SSRs entered by the user', required=False)
    ssr_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)


class BOPSearchForm(DocumentWithLiteratureSearchForm):
    parent = forms.CharField(help_text='Parent BOP', required=False)
    parent_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    building_sed = forms.CharField(help_text="Building SED", required=False)
    building_sed_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)


class BrainRegionSearchForm(SearchForm):
    name = forms.CharField(help_text="Brain region name", required=False)
    name_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    abbreviation = forms.CharField(help_text="Brain region abbreviation", required=False)
    abbreviation_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    parent = forms.CharField(help_text="Brain region parent", required=False)
    parent_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    nomenclature = forms.CharField(help_text="Nomenclature that the brain region belongs to", required=False)
    nomenclature_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    species = forms.CharField(help_text="Species that the brain region applies to", required=False)
    species_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    region_type = forms.ChoiceField(choices=BrainRegion.REGION_TYPE_CHOICES, help_text="Type of brain region",
        required=False)


class LiteratureSearchForm(SearchForm):
    title = forms.CharField(help_text="Literature title", required=False)
    title_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    author = forms.CharField(help_text="Literature authors", required=False)
    author_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    type = forms.ChoiceField(choices=Literature.TYPE_CHOICES, help_text="Type of literature entry", required=False)
    year_min = forms.CharField(help_text="Literature min year", required=False)
    year_max = forms.CharField(help_text="Literature max year", required=False)
    annotation = forms.CharField(help_text="Literature annotation", required=False)
    annotation_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    collator = forms.BooleanField(help_text="Only search your entries", required=False)
    username = forms.CharField(help_text='Username of the collator',required=False)
    first_name = forms.CharField(help_text='First name of the collator',required=False)
    last_name = forms.CharField(help_text='First name of the collator',required=False)
    created_from = forms.DateTimeField(help_text="Earliest creation date", widget=forms.DateTimeInput, required=False)
    created_to = forms.DateTimeField(help_text="Latest creation date", widget=forms.DateTimeInput, required=False)


class ModelSearchForm(DocumentWithLiteratureSearchForm):
    author = forms.CharField(help_text="Model author", required=False)
    author_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    building_sed = forms.CharField(help_text="Building SED", required=False)
    building_sed_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    testing_sed = forms.CharField(help_text="Testing SED", required=False)
    testing_sed_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    prediction = forms.CharField(help_text="Prediction", required=False)
    prediction_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    ssr = forms.CharField(help_text="SSR", required=False)
    ssr_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)


class SEDSearchForm(DocumentWithLiteratureSearchForm):
    METHOD_CHOICES = (
        ('', ''),
        ('fMRI', 'fMRI'),
        ('PET', 'PET'),
        )
    LATENCY_CHOICES = (
        ('', ''),
        ('exact', 'Exact'),
        ('approx', 'Approximate'),
        ('window', 'Time Window')
        )
    type = forms.ChoiceField(choices=SED.TYPE_CHOICES, help_text='Type of SED', required=False,
        widget=forms.Select(attrs={'onchange': 'updateSEDSearchOptions(this.value)'}))
    control_condition = forms.CharField(help_text='Control condition', required=False)
    control_condition_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    experimental_condition = forms.CharField(help_text='Experimental condition', required=False)
    experimental_condition_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    method = forms.ChoiceField(choices=METHOD_CHOICES, help_text='Method', required=False)
    coordinate_brain_region = forms.CharField(help_text='Coordinate brain region', required=False)
    coordinate_brain_region_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    x_min = forms.CharField(help_text='Minimum x coordinate', widget=forms.TextInput(attrs={'size':'3'}),
        required=False)
    x_max = forms.CharField(help_text='Maximum x coordinate', widget=forms.TextInput(attrs={'size':'3'}),
        required=False)
    y_min = forms.CharField(help_text='Minimum y coordinate', widget=forms.TextInput(attrs={'size':'3'}),
        required=False)
    y_max = forms.CharField(help_text='Maximum y coordinate', widget=forms.TextInput(attrs={'size':'3'}),
        required=False)
    z_min = forms.CharField(help_text='Minimum z coordinate', widget=forms.TextInput(attrs={'size':'3'}),
        required=False)
    z_max = forms.CharField(help_text='Maximum z coordinate', widget=forms.TextInput(attrs={'size':'3'}),
        required=False)
    source_region = forms.CharField(help_text='Connection source brain region', required=False)
    source_region_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    source_region_nomenclature = forms.CharField(help_text='Connection source brain region nomenclature',
        required=False)
    source_region_nomenclature_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    target_region = forms.CharField(help_text='Connection target brain region', required=False)
    target_region_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    target_region_nomenclature = forms.CharField(help_text='Connection target brain region nomenclature',
        required=False)
    target_region_nomenclature_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    connection_region = forms.CharField(help_text='Connection source or target brain region', required=False)
    connection_region_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    connection_region_nomenclature = forms.CharField(help_text='Connection source or target brain region nomenclature',
        required=False)
    connection_region_nomenclature_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    cognitive_paradigm=forms.CharField(help_text='Cognitive paradigm', required=False)
    cognitive_paradigm_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    sensory_modality=forms.CharField(help_text='Sensory modality', required=False)
    sensory_modality_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    response_modality=forms.CharField(help_text='Response modality', required=False)
    response_modality_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    erp_control_condition=forms.CharField(help_text='Control condition', required=False)
    erp_control_condition_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    erp_experimental_condition=forms.CharField(help_text='Experimental condition', required=False)
    erp_experimental_condition_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    erp_component_name=forms.CharField(help_text='ERP component name', required=False)
    erp_component_name_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    latency_peak_min=forms.CharField(help_text='Minimum peak latency', widget=forms.TextInput(attrs={'size':'5'}),
        required=False)
    latency_peak_max=forms.CharField(help_text='Maximum peak latency', widget=forms.TextInput(attrs={'size':'5'}),
        required=False)
    latency_peak_type=forms.ChoiceField(choices=LATENCY_CHOICES, help_text='Type of peak latency', required=False)
    latency_onset_min=forms.CharField(help_text='Minimum peak latency onset',
        widget=forms.TextInput(attrs={'size':'5'}), required=False)
    latency_onset_max=forms.CharField(help_text='Maximum peak latency onset',
        widget=forms.TextInput(attrs={'size':'5'}), required=False)
    amplitude_peak_min=forms.CharField(help_text='Minimum amplitude peak', widget=forms.TextInput(attrs={'size':'5'}),
        required=False)
    amplitude_peak_max=forms.CharField(help_text='Maximum amplitude peak', widget=forms.TextInput(attrs={'size':'5'}),
        required=False)
    amplitude_mean_min=forms.CharField(help_text='Minimum amplitude mean', widget=forms.TextInput(attrs={'size':'5'}),
        required=False)
    amplitude_mean_max=forms.CharField(help_text='Maximum amplitude mean', widget=forms.TextInput(attrs={'size':'5'}),
        required=False)
    scalp_region=forms.CharField(help_text='Scalp region', required=False)
    scalp_region_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    electrode_cap=forms.CharField(help_text='Electrode cap', required=False)
    electrode_cap_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    electrode_name=forms.CharField(help_text='Electrode name', required=False)
    electrode_name_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    source=forms.CharField(help_text='Source', required=False)
    source_options=forms.ChoiceField(choices=SEARCH_CHOICES, help_text='Search options', required=False)
    search_cocomac = forms.BooleanField(help_text='Search CoCoMac',required=False)
    search_brede = forms.BooleanField(help_text='Search Brede', required=False)


class PubmedSearchForm(forms.Form):
    all = forms.CharField(help_text='All fields', required=False)
    title = forms.CharField(help_text='Title', required=False)
    authors = forms.CharField(help_text='Authors', required=False)
    journal = forms.CharField(help_text='Journal', required=False)
    volume = forms.CharField(help_text='Volume', required=False)
    issue = forms.CharField(help_text='Issue', required=False)
    min_year = forms.CharField(help_text='From year', required=False)
    max_year = forms.CharField(help_text='To year', required=False)
    start = forms.IntegerField(widget=forms.HiddenInput)


class ModelDBSearchForm(forms.Form):
    all = forms.CharField(help_text='All fields', required=False)


