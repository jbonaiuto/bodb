from django import forms
from django.contrib.auth.models import Group
from django.forms.models import ErrorList, inlineformset_factory, modelformset_factory, formset_factory
from bodb.models import BOP, DocumentFigure, Document, RelatedBOP, LiteratureAuthor, Journal, Book, Chapter, Conference, Thesis, Unpublished, Author, Literature, BrainRegion, RelatedBrainRegion, ModelAuthor, Model, Variable, Module, RelatedModel, BrainRegionRequest, ERPSED, CoordinateSpace, BrainImagingSED, SEDCoord, Nomenclature, ElectrodePositionSystem, ElectrodePosition
from bodb.models.discussion import Post, Forum
from bodb.models.messaging import Subscription, UserSubscription, Message
from bodb.models.sed import SED, BuildSED, TestSED, TestSEDSSR, ERPComponent, ConnectivitySED, ElectrodeCap
from bodb.models.ssr import Prediction, SSR, PredictionSSR
from bodb.models.workspace import BodbProfile, Workspace, WorkspaceBookmark
from registration.forms import RegistrationForm
from registration.models import User
from taggit.forms import TagField
from uscbp.forms import nested_formset_factory
from uscbp.widgets import ImageWidget

class UserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.order_by('name'),
        widget=forms.SelectMultiple(attrs={'size':'5'}),
        help_text='Hold down "Control", or "Command" on a Mac, to select more than one.',
        required=False)
    class Meta:
        model = User
        exclude=('last_login', 'date_joined', 'password')


class WorkspaceUserForm(forms.ModelForm):
    class Meta:
        model = User
        exclude=('last_login', 'date_joined', 'password', 'groups','username')


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group


class BodbRegistrationForm(RegistrationForm):
    """
    Extends the basic registration form with support for fields required by BODB.
        - first_name, last_name, and affiliation
    """
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    affiliation = forms.CharField(required=True)

    def save(self, profile_callback=None):
        """
        Override RegistrationForm.save() so that we can commit the first_name and last_name to the
        user object and the affiliation to the user profile object.
        """

        # First, save the parent form
        new_user = super(BodbRegistrationForm, self).save(profile_callback=profile_callback)

        # Update user with first, last names
        new_user.first_name = self.cleaned_data['first_name']
        new_user.last_name = self.cleaned_data['last_name']
        new_user.save()

        # Update profile with affiliation
        profile = new_user.get_profile()
        profile.affiliation = self.cleaned_data['affiliation']
        profile.save()

        return new_user

class BodbProfileForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    avatar=forms.ImageField(required=False, widget=ImageWidget)
    password1 = forms.CharField(widget=forms.PasswordInput(render_value=False),required=False)
    password2 = forms.CharField(widget=forms.PasswordInput(render_value=False),required=False)
    notification_preference = forms.ChoiceField(choices=BodbProfile.NOTIFICATION_TYPE_CHOICES, help_text="Notification preference",
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}),
        required=True)
    affiliation = forms.CharField(required=True)

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(u'You must type the same password each time')
        return self.cleaned_data

    class Meta:
        model=BodbProfile
        exclude=('active_workspace','loaded_coordinate_selection','favorites')


SubscriptionFormSet = inlineformset_factory(User, Subscription, fk_name='user', extra=0, can_delete=True)
UserSubscriptionFormSet = inlineformset_factory(User, UserSubscription, fk_name='user', extra=0, can_delete=True)


class SubscriptionForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput, required=False)
    model_type = forms.ChoiceField(choices=Subscription.MODEL_TYPE_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=True)
    keywords = forms.CharField(required=True)

    class Meta:
        model=Subscription


class UserSubscriptionForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput, required=False)
    subscribed_to_user = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput, required=True)
    model_type = forms.ChoiceField(choices=Subscription.MODEL_TYPE_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=True)
    keywords = forms.CharField(help_text='Keywords', required=False)

    class Meta:
        model=UserSubscription


class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=User.objects.all(),
        widget=forms.Select(attrs={'onchange':"selectRecipient(this.value);"}),
        required=True)
    subject = forms.CharField(widget=forms.TextInput(attrs={'size':'37'}))
    text = forms.CharField(widget=forms.Textarea(attrs={'cols':'57'}),required=True)

    def __init__(self, user=None, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None):
        self.base_fields['recipient'].queryset=User.objects.exclude(id=user.id)
        super(MessageForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix,
            empty_permitted, instance)

    class Meta:
        model=Message
        exclude=('read', 'sender')


class PostForm(forms.ModelForm):
    forum = forms.ModelChoiceField(queryset=Forum.objects.all(),widget=forms.HiddenInput,required=False)
    parent = forms.ModelChoiceField(queryset=Post.objects.all(),widget=forms.HiddenInput,required=False)
    author = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    body = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)
    class Meta:
        model=Post


class BrainRegionRequestForm(forms.ModelForm):
    user=forms.ModelChoiceField(User.objects.all(),widget=forms.HiddenInput,required=False)
    name = forms.CharField(widget=forms.TextInput(attrs={'size':'20'}),required=True)
    abbreviation = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    parent = forms.CharField(widget=forms.TextInput(attrs={'size':'20'}),required=False)
    children = forms.CharField(widget=forms.TextInput(attrs={'size':'20'}),required=False)
    nomenclature = forms.CharField(widget=forms.TextInput(attrs={'size':'20'}),required=True)
    nomenclature_version = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    rationale = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)

    class Meta:
        model = BrainRegionRequest
        exclude=('activation_key','status')


class BrainRegionRequestDenyForm(forms.Form):
    reason=forms.CharField(widget=forms.Textarea(attrs={'cols':'57', 'rows':'5'}), required=True)


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


class AllSearchForm(forms.Form):
    PUBLIC_CHOICES = (
        ('', ''),
        ('True', 'True'),
        ('False', 'False'),
        )
    public = forms.ChoiceField(choices=PUBLIC_CHOICES, help_text='Public entries', required=False)
    keywords = forms.CharField(help_text="Keyword search", required=False)
    title = forms.CharField(help_text="Title", required=False)
    description = forms.CharField(help_text="Description", required=False)
    narrative = forms.CharField(help_text="Narrative", required=False)
    tags = TagField(required=False)
    created_from = forms.DateTimeField(help_text="Earliest creation date", widget=forms.DateTimeInput, required=False)
    created_to = forms.DateTimeField(help_text="Latest creation date", widget=forms.DateTimeInput, required=False)
    collator = forms.BooleanField(help_text="Only search your entries", required=False)
    username = forms.CharField(help_text='Username of the collator',required=False)
    first_name = forms.CharField(help_text='First name of the collator',required=False)
    last_name = forms.CharField(help_text='First name of the collator',required=False)
    search_cocomac = forms.BooleanField(help_text='Search CoCoMac',required=False)
    search_brede = forms.BooleanField(help_text='Search Brede', required=False)


class BOPSearchForm(forms.Form):
    PUBLIC_CHOICES = (
        ('', ''),
        ('True', 'True'),
        ('False', 'False'),
        )
    public = forms.ChoiceField(choices=PUBLIC_CHOICES, help_text='Public BOPs', required=False)
    keywords = forms.CharField(help_text="Keyword search of BOP", required=False)
    title = forms.CharField(help_text="BOP title", required=False)
    description = forms.CharField(help_text="BOP description", required=False)
    narrative = forms.CharField(help_text="BOP narrative", required=False)
    parent = forms.CharField(help_text='Parent BOP', required=False)
    tags = TagField(required=False)
    related_brain_region = forms.CharField(help_text='Related brain region', required=False)
    collator = forms.BooleanField(help_text="Only search your entries", required=False)
    username = forms.CharField(help_text='Username of the collator',required=False)
    first_name = forms.CharField(help_text='First name of the collator',required=False)
    last_name = forms.CharField(help_text='First name of the collator',required=False)
    created_from = forms.DateTimeField(help_text="Earliest creation date", widget=forms.DateTimeInput, required=False)
    created_to = forms.DateTimeField(help_text="Latest creation date", widget=forms.DateTimeInput, required=False)
    related_literature_title = forms.CharField(help_text="Related literature title", required=False)
    related_literature_author = forms.CharField(help_text="Related literature author", required=False)
    related_literature_year_min = forms.CharField(help_text="Related literature min year", required=False)
    related_literature_year_max = forms.CharField(help_text="Related literature max year", required=False)
    related_literature_annotation = forms.CharField(help_text="Related literature annotation", required=False)
    building_sed = forms.CharField(help_text="Building SED", required=False)
    related_bop = forms.CharField(help_text="Related BOP", required=False)
    related_model = forms.CharField(help_text="Related_Model", required=False)


class BrainRegionSearchForm(forms.Form):
    keywords = forms.CharField(help_text="Keyword search of name and abbreviation, and nomenclature", required=False)
    name = forms.CharField(help_text="Brain region name", required=False)
    abbreviation = forms.CharField(help_text="Brain region abbreviation", required=False)
    parent = forms.CharField(help_text="Brain region parent", required=False)
    nomenclature = forms.CharField(help_text="Nomenclature that the brain region belongs to", required=False)
    species = forms.CharField(help_text="Species that the brain region applies to", required=False)
    region_type = forms.ChoiceField(choices=BrainRegion.REGION_TYPE_CHOICES, help_text="Type of brain region",
        required=False)


class LiteratureSearchForm(forms.Form):
    keywords = forms.CharField(help_text="Keyword search of literature", required=False)
    title = forms.CharField(help_text="Literature title", required=False)
    author = forms.CharField(help_text="Literature authors", required=False)
    type = forms.ChoiceField(choices=Literature.TYPE_CHOICES, help_text="Type of literature entry", required=False)
    year_min = forms.CharField(help_text="Literature min year", required=False)
    year_max = forms.CharField(help_text="Literature max year", required=False)
    annotation = forms.CharField(help_text="Literature annotation", required=False)
    collator = forms.BooleanField(help_text="Only search your entries", required=False)
    username = forms.CharField(help_text='Username of the collator',required=False)
    first_name = forms.CharField(help_text='First name of the collator',required=False)
    last_name = forms.CharField(help_text='First name of the collator',required=False)
    created_from = forms.DateTimeField(help_text="Earliest creation date", widget=forms.DateTimeInput, required=False)
    created_to = forms.DateTimeField(help_text="Latest creation date", widget=forms.DateTimeInput, required=False)


class ModelSearchForm(forms.Form):
    PUBLIC_CHOICES = (
        ('', ''),
        ('True', 'True'),
        ('False', 'False'),
        )
    public = forms.ChoiceField(choices=PUBLIC_CHOICES, help_text='Public Models', required=False)
    keywords = forms.CharField(help_text="Keyword search of Model", required=False)
    title = forms.CharField(help_text="Model title", required=False)
    author = forms.CharField(help_text="Model author", required=False)
    description = forms.CharField(help_text="Model description", required=False)
    narrative = forms.CharField(help_text="Model narrative", required=False)
    tags = TagField(required=False)
    related_brain_region = forms.CharField(help_text='Related brain region', required=False)
    building_sed = forms.CharField(help_text="Building SED", required=False)
    testing_sed = forms.CharField(help_text="Testing SED", required=False)
    prediction = forms.CharField(help_text="Prediction", required=False)
    ssr = forms.CharField(help_text="SSR", required=False)
    related_bop = forms.CharField(help_text="Related BOP", required=False)
    related_model = forms.CharField(help_text="Related_Model", required=False)
    username = forms.CharField(help_text='Username of the collator',required=False)
    first_name = forms.CharField(help_text='First name of the collator',required=False)
    last_name = forms.CharField(help_text='First name of the collator',required=False)
    collator = forms.BooleanField(help_text="Only search your entries", required=False)
    created_from = forms.DateTimeField(help_text="Earliest creation date", widget=forms.DateTimeInput, required=False)
    created_to = forms.DateTimeField(help_text="Latest creation date", widget=forms.DateTimeInput, required=False)
    related_literature_title = forms.CharField(help_text="Related literature title", required=False)
    related_literature_author = forms.CharField(help_text="Related literature author", required=False)
    related_literature_year_min = forms.CharField(help_text="Related literature min year", required=False)
    related_literature_year_max = forms.CharField(help_text="Related literature max year", required=False)
    related_literature_annotation = forms.CharField(help_text="Related literature annotation", required=False)


class SEDSearchForm(forms.Form):
    PUBLIC_CHOICES = (
        ('', ''),
        ('True', 'True'),
        ('False', 'False'),
        )
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
    public = forms.ChoiceField(choices=PUBLIC_CHOICES, help_text='Public SEDs', required=False)
    keywords = forms.CharField(help_text="Keyword search of SED", required=False)
    title = forms.CharField(help_text="SED title", required=False)
    description = forms.CharField(help_text="SED description", required=False)
    narrative = forms.CharField(help_text="SED narrative", required=False)
    type = forms.ChoiceField(choices=SED.TYPE_CHOICES, help_text='Type of SED', required=False,
        widget=forms.Select(attrs={'onchange': 'updateSEDSearchOptions(this.value)'}))
    tags = TagField(required=False)
    related_brain_region = forms.CharField(help_text='Related brain region', required=False)
    created_from = forms.DateTimeField(help_text="Earliest creation date", widget=forms.DateTimeInput, required=False)
    created_to = forms.DateTimeField(help_text="Latest creation date", widget=forms.DateTimeInput, required=False)
    username = forms.CharField(help_text='Username of the collator',required=False)
    first_name = forms.CharField(help_text='First name of the collator',required=False)
    last_name = forms.CharField(help_text='First name of the collator',required=False)
    collator = forms.BooleanField(help_text="Only search your entries", required=False)
    related_literature_title = forms.CharField(help_text="Related literature title", required=False)
    related_literature_author = forms.CharField(help_text="Related literature author", required=False)
    related_literature_year_min = forms.CharField(help_text="Related literature min year", required=False)
    related_literature_year_max = forms.CharField(help_text="Related literature max year", required=False)
    related_literature_annotation = forms.CharField(help_text="Related literature annotation", required=False)
    control_condition = forms.CharField(help_text='Control condition', required=False)
    experimental_condition = forms.CharField(help_text='Experimental condition', required=False)
    method = forms.ChoiceField(choices=METHOD_CHOICES, help_text='Method', required=False)
    coordinate_brain_region = forms.CharField(help_text='Coordinate brain region', required=False)
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
    source_region_nomenclature = forms.CharField(help_text='Connection source brain region nomenclature',
        required=False)
    target_region = forms.CharField(help_text='Connection target brain region', required=False)
    target_region_nomenclature = forms.CharField(help_text='Connection target brain region nomenclature',
        required=False)
    connection_region = forms.CharField(help_text='Connection source or target brain region', required=False)
    connection_region_nomenclature = forms.CharField(help_text='Connection source or target brain region nomenclature',
        required=False)
    cognitive_paradigm=forms.CharField(help_text='Cognitive paradigm', required=False)
    sensory_modality=forms.CharField(help_text='Sensory modality', required=False)
    response_modality=forms.CharField(help_text='Response modality', required=False)
    erp_control_condition=forms.CharField(help_text='Control condition', required=False)
    erp_experimental_condition=forms.CharField(help_text='Experimental condition', required=False)
    erp_component_name=forms.CharField(help_text='ERP component name', required=False)
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
    electrode_cap=forms.CharField(help_text='Electrode cap', required=False)
    electrode_name=forms.CharField(help_text='Electrode name', required=False)
    source=forms.CharField(help_text='Source', required=False)
    search_cocomac = forms.BooleanField(help_text='Search CoCoMac',required=False)
    search_brede = forms.BooleanField(help_text='Search Brede', required=False)


class SSRSearchForm(forms.Form):
    PUBLIC_CHOICES = (
        ('', ''),
        ('True', 'True'),
        ('False', 'False'),
        )
    public = forms.ChoiceField(choices=PUBLIC_CHOICES, help_text='Public SSRs', required=False)
    keywords = forms.CharField(help_text="Keyword search of SSR", required=False)
    title = forms.CharField(help_text="SSR title", required=False)
    description = forms.CharField(help_text="SSR description", required=False)
    narrative = forms.CharField(help_text="SSR narrative", required=False)
    tags = TagField(required=False)
    username = forms.CharField(help_text='Username of the collator',required=False)
    first_name = forms.CharField(help_text='First name of the collator',required=False)
    last_name = forms.CharField(help_text='First name of the collator',required=False)
    collator = forms.BooleanField(help_text="Only search your entries", required=False)
    created_from = forms.DateTimeField(help_text="Earliest creation date", widget=forms.DateTimeInput, required=False)
    created_to = forms.DateTimeField(help_text="Latest creation date", widget=forms.DateTimeInput, required=False)


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


class BOPForm(forms.ModelForm):
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    parent = forms.ModelChoiceField(queryset=BOP.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(help_text='Make the entry public', required=False)
    literature = forms.ModelMultipleChoiceField(queryset=Literature.objects.order_by('title'),
        widget=forms.MultipleHiddenInput, required=False)
    tags = TagField(required=False)

    def clean(self):
        if self.data['draft']!='1':
            return super(BOPForm, self).clean()
        else:
            self._errors.clear()
        return self.cleaned_data

    class Meta:
        model=BOP


class DocumentFigureForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    figure=forms.ImageField(required=True, widget=ImageWidget)
    title=forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    caption=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    order=forms.IntegerField(widget=forms.TextInput(attrs={'size':'3'}),required=True)

    class Meta:
        model=DocumentFigure


DocumentFigureFormSet = inlineformset_factory(Document, DocumentFigure, form=DocumentFigureForm, fk_name='document',
    extra=0, can_delete=True, can_order=True)


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

class JournalForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(queryset=LiteratureAuthor.objects.order_by('order'),
        widget=forms.MultipleHiddenInput, required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}))
    year = forms.CharField(widget=forms.TextInput(attrs={'size':'4'}))
    journal_name = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),label='Journal')
    annotation = forms.CharField(widget=forms.Textarea(attrs={'cols':'57'}),required=False)
    collator=forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    pubmed_id=forms.CharField(widget=forms.HiddenInput,required=False)
    class Meta:
        model = Journal
        exclude = ('literature_ptr',)


class BookForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(queryset=LiteratureAuthor.objects.order_by('order'),
        widget=forms.MultipleHiddenInput, required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}))
    year = forms.CharField(widget=forms.TextInput(attrs={'size':'4'}))
    annotation = forms.CharField(widget=forms.Textarea(attrs={'cols':'57'}),required=False)
    collator=forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    pubmed_id=forms.CharField(widget=forms.HiddenInput,required=False)
    class Meta:
        model = Book
        exclude = ('literature_ptr',)


class ChapterForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(queryset=LiteratureAuthor.objects.order_by('order'),
        widget=forms.MultipleHiddenInput, required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}))
    book_title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}))
    year = forms.CharField(widget=forms.TextInput(attrs={'size':'4'}))
    annotation = forms.CharField(widget=forms.Textarea(attrs={'cols':'57'}),required=False)
    collator=forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    pubmed_id=forms.CharField(widget=forms.HiddenInput,required=False)
    class Meta:
        model = Chapter
        exclude = ('literature_ptr',)


class ConferenceForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(queryset=LiteratureAuthor.objects.order_by('order'),
        widget=forms.MultipleHiddenInput, required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}))
    year = forms.CharField(widget=forms.TextInput(attrs={'size':'4'}))
    annotation = forms.CharField(widget=forms.Textarea(attrs={'cols':'57'}),required=False)
    collator=forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    pubmed_id=forms.CharField(widget=forms.HiddenInput,required=False)
    class Meta:
        model = Conference
        exclude = ('literature_ptr',)


class ThesisForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(queryset=LiteratureAuthor.objects.order_by('order'),
        widget=forms.MultipleHiddenInput, required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}))
    year = forms.CharField(widget=forms.TextInput(attrs={'size':'4'}))
    annotation = forms.CharField(widget=forms.Textarea(attrs={'cols':'57'}),required=False)
    collator=forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    pubmed_id=forms.CharField(widget=forms.HiddenInput,required=False)
    class Meta:
        model = Thesis
        exclude = ('literature_ptr',)


class UnpublishedForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(queryset=LiteratureAuthor.objects.order_by('order'),
        widget=forms.MultipleHiddenInput, required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}))
    year = forms.CharField(widget=forms.TextInput(attrs={'size':'4'}))
    annotation = forms.CharField(widget=forms.Textarea(attrs={'cols':'57'}),required=False)
    collator=forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    pubmed_id=forms.CharField(widget=forms.HiddenInput,required=False)
    class Meta:
        model = Unpublished
        exclude = ('literature_ptr',)


class LiteratureAuthorInlineForm(forms.ModelForm):
    author_first_name = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=True)
    author_middle_name = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    author_last_name = forms.CharField(widget=forms.TextInput(attrs={'size':'26'}),required=True)
    author_alias = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=False)
    author_email = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    author_homepage = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=False)
    author = forms.ModelChoiceField(queryset=Author.objects.all(),widget=forms.HiddenInput,required=False)
    order = forms.CharField(widget=forms.TextInput(attrs={'size':'3'}),required=True)

    def __init__(self, *args, **kwargs):
        super(LiteratureAuthorInlineForm, self).__init__(*args, **kwargs)
        instance=kwargs.get('instance')
        if instance is not None and instance.author is not None:
            self.initial['author_first_name']=instance.author.first_name
            self.initial['author_middle_name']=instance.author.middle_name
            self.initial['author_last_name']=instance.author.last_name
            self.initial['author_alias']=instance.author.alias
            self.initial['author_email']=instance.author.email
            self.initial['author_homepage']=instance.author.homepage

    class Meta:
        model = LiteratureAuthor


LiteratureAuthorFormSet=modelformset_factory(LiteratureAuthor, form=LiteratureAuthorInlineForm,
    can_delete=True, extra=0, exclude=('author',))


class SEDForm(forms.ModelForm):
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(help_text='Make the entry public', required=False)
    type=forms.CharField(widget=forms.HiddenInput,required=False)
    literature = forms.ModelMultipleChoiceField(queryset=Literature.objects.order_by('title'),
        widget=forms.MultipleHiddenInput, required=False)
    tags = TagField(required=False)

    def clean(self):
        if self.data['draft']!='1':
            return super(SEDForm, self).clean()
        else:
            self._errors.clear()
        return self.cleaned_data

    class Meta:
        model=SED


class ConnectivitySEDForm(forms.ModelForm):
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    source_region = forms.ModelChoiceField(queryset=BrainRegion.objects.all(), widget=forms.HiddenInput, required=True)
    target_region = forms.ModelChoiceField(queryset=BrainRegion.objects.all(), widget=forms.HiddenInput, required=True)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(help_text='Make the entry public', required=False)
    type=forms.CharField(widget=forms.HiddenInput,required=False)
    literature = forms.ModelMultipleChoiceField(queryset=Literature.objects.order_by('title'),
        widget=forms.MultipleHiddenInput, required=False)
    tags=TagField(required=False)

    def clean(self):
        if self.data['draft']!='1':
            return super(ConnectivitySEDForm, self).clean()
        else:
            self._errors.clear()
        return self.cleaned_data

    class Meta:
        model=ConnectivitySED


class ERPSEDForm(forms.ModelForm):
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    cognitive_paradigm = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}), required=False)
    sensory_modality = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}), required=False)
    response_modality = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}), required=False)
    control_condition = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    experimental_condition = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(help_text='Make the entry public', required=False)
    type=forms.CharField(widget=forms.HiddenInput,required=False)
    literature = forms.ModelMultipleChoiceField(queryset=Literature.objects.order_by('title'),
        widget=forms.MultipleHiddenInput, required=False)
    tags=TagField(required=False)

    def clean(self):
        if self.data['draft']!='1':
            return super(ERPSEDForm, self).clean()
        else:
            self._errors.clear()
        return self.cleaned_data

    class Meta:
        model=ERPSED


class ERPComponentInlineForm(forms.ModelForm):
    erp_sed = forms.ModelChoiceField(queryset=ERPSED.objects.all(),widget=forms.HiddenInput,required=False)
    component_name=forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    latency_peak=forms.DecimalField(widget=forms.TextInput(attrs={'size':'10'}), required=True)
    latency_peak_type=forms.ChoiceField(choices=ERPComponent.LATENCY_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=True)
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
    interpretation=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)

    class Meta:
        model=ERPComponent


ERPComponentFormSet = inlineformset_factory(ERPSED, ERPComponent, form=ERPComponentInlineForm, fk_name='erp_sed',
    extra=0, can_delete=True)


class BrainImagingSEDForm(forms.ModelForm):
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    control_condition = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    experimental_condition = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    coord_space = forms.ModelChoiceField(CoordinateSpace.objects.all(), required=True)
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
    data = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'10'}),required=True)
    literature = forms.ModelMultipleChoiceField(queryset=Literature.objects.order_by('title'),
        widget=forms.MultipleHiddenInput, required=False)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    tags=TagField(required=False)
    public = forms.BooleanField(help_text='Make the entry public', required=False)
    type=forms.CharField(widget=forms.HiddenInput,required=False)

    def clean(self):
        if self.data['draft']!='1':
            return super(BrainImagingSEDForm, self).clean()
        else:
            self._errors.clear()
        return self.cleaned_data

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


class RelatedBrainRegionInlineForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    relationship = forms.CharField(widget=forms.Textarea(attrs={'cols':'40','rows':'3'}),required=True)
    brain_region = forms.ModelChoiceField(queryset=BrainRegion.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model=RelatedBrainRegion


RelatedBrainRegionFormSet = inlineformset_factory(Document,RelatedBrainRegion,form=RelatedBrainRegionInlineForm,
    fk_name='document',extra=0, can_delete=True)


class ModelForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    authors = forms.ModelMultipleChoiceField(queryset=ModelAuthor.objects.order_by('order'),
        widget=forms.MultipleHiddenInput, required=False)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)
    execution_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    documentation_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    description_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    simulation_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    modeldb_accession_number = forms.IntegerField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    literature = forms.ModelMultipleChoiceField(queryset=Literature.objects.order_by('title'),
        widget=forms.MultipleHiddenInput, required=False)
    public = forms.BooleanField(help_text='Make the entry public', required=False)
    tags = TagField(required=False)

    def clean(self):
        if self.data['draft']!='1':
            return super(ModelForm, self).clean()
        else:
            self._errors.clear()
        return self.cleaned_data

    class Meta:
        model = Model


class ModuleForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    parent = forms.ModelChoiceField(queryset=Module.objects.all(), widget=forms.HiddenInput,required=True)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(help_text='Make the entry public', required=False)
    tags = TagField(required=False)

    def clean(self):
        if self.data['draft']!='1':
            return super(ModuleForm, self).clean()
        else:
            self._errors.clear()
        return self.cleaned_data

    class Meta:
        model = Module


class ModelAuthorInlineForm(forms.ModelForm):
    author_first_name = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=True)
    author_middle_name = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    author_last_name = forms.CharField(widget=forms.TextInput(attrs={'size':'26'}),required=True)
    author_alias = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=False)
    author_email = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    author_homepage = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=False)
    author = forms.ModelChoiceField(queryset=Author.objects.all(),widget=forms.HiddenInput,required=False)
    order = forms.CharField(widget=forms.TextInput(attrs={'size':'3'}),required=True)

    def __init__(self, *args, **kwargs):
        super(ModelAuthorInlineForm, self).__init__(*args, **kwargs)
        instance=kwargs.get('instance')
        if instance is not None and instance.author is not None:
            self.initial['author_first_name']=instance.author.first_name
            self.initial['author_middle_name']=instance.author.middle_name
            self.initial['author_last_name']=instance.author.last_name
            self.initial['author_alias']=instance.author.alias
            self.initial['author_email']=instance.author.email
            self.initial['author_homepage']=instance.author.homepage

    class Meta:
        model = ModelAuthor


ModelAuthorFormSet=modelformset_factory(ModelAuthor, form=ModelAuthorInlineForm, can_delete=True, extra=0,
    exclude=('author',))


class VariableInlineForm(forms.ModelForm):
    module = forms.ModelChoiceField(queryset=Module.objects.all(),widget=forms.HiddenInput,required=False)
    name = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=True)
    data_type = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}),required=True)
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'42','rows':'3'}),required=True)
    var_type = forms.CharField(widget=forms.HiddenInput,required=True)
    class Meta:
        model=Variable


VariableFormSet = inlineformset_factory(Module,Variable,form=VariableInlineForm, fk_name='module',extra=0,
    can_delete=True)


class ModuleInlineForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'47','rows':'3'}),required=True)
    collator=forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    draft=forms.BooleanField(widget=forms.HiddenInput,required=False)
    public=forms.BooleanField(widget=forms.HiddenInput,required=False)

    class Meta:
        model = Module
        exclude=('tags',)


ModuleFormSet=inlineformset_factory(Module, Module, form=ModuleInlineForm, fk_name='parent', can_delete=True, extra=0)


class RelatedModelInlineForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    relationship = forms.CharField(widget=forms.Textarea(attrs={'cols':'40','rows':'3'}),required=True)
    model = forms.ModelChoiceField(queryset=Model.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model=RelatedModel


RelatedModelFormSet = inlineformset_factory(Document,RelatedModel,form=RelatedModelInlineForm,fk_name='document',extra=0,
    can_delete=True)


class BuildSEDInlineForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    sed = forms.ModelChoiceField(queryset=SED.objects.all(),widget=forms.HiddenInput,required=False)
    relationship = forms.ChoiceField(choices=BuildSED.RELATIONSHIP_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=True)
    relevance_narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'37','rows':'3'}),required=True)

    class Meta:
        model=BuildSED


BuildSEDFormSet = inlineformset_factory(Document,BuildSED,form=BuildSEDInlineForm, fk_name='document',extra=0,
    can_delete=True)


class TestSEDInlineForm(forms.ModelForm):
    model = forms.ModelChoiceField(queryset=Model.objects.all(),widget=forms.HiddenInput,required=False)
    sed = forms.ModelChoiceField(queryset=SED.objects.all(),widget=forms.HiddenInput,required=False)
    relationship = forms.ChoiceField(choices=TestSED.RELATIONSHIP_CHOICES,
        widget=forms.Select(attrs={'style': 'font-size: 80%;font-family: verdana, sans-serif'}), required=True)
    relevance_narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'37','rows':'3'}),required=True)

    class Meta:
        model=TestSED


class TestSEDSSRInlineForm(forms.ModelForm):
    test_sed = forms.ModelChoiceField(queryset=TestSED.objects.all(),widget=forms.HiddenInput,required=False)
    ssr = forms.ModelChoiceField(queryset=SSR.objects.all(),widget=forms.HiddenInput,required=False)
    ssr_collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    ssr_title = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=True)
    ssr_brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'50','rows':'3'}),required=True)
    ssr_draft=forms.CharField(widget=forms.HiddenInput,required=False)
    ssr_public = forms.BooleanField(widget=forms.HiddenInput, required=False)
    ssr_type=forms.CharField(widget=forms.HiddenInput,required=False)

    def __init__(self, *args, **kwargs):
        super(TestSEDSSRInlineForm, self).__init__(*args, **kwargs)
        instance=kwargs.get('instance')
        if instance is not None and instance.ssr is not None:
            self.initial['ssr_collator']=instance.ssr.collator
            self.initial['ssr_title']=instance.ssr.title
            self.initial['ssr_brief_description']=instance.ssr.brief_description
            self.initial['ssr_draft']=instance.ssr.draft
            self.initial['ssr_public']=instance.ssr.public
            self.initial['ssr_type']=instance.ssr.type

    class Meta:
        model = TestSEDSSR


TestSEDFormSet = nested_formset_factory(Model,TestSED,TestSEDSSR,form=TestSEDInlineForm,
    nested_form=TestSEDSSRInlineForm,fk_name='model',nested_fk_name='test_sed',can_delete=True,
    nested_can_delete=True,extra=0,nested_extra=1,nested_max_num=1)


class PredictionForm(forms.ModelForm):
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
    ssr_title = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=True)
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


class SSRForm(forms.ModelForm):
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)
    draft=forms.CharField(widget=forms.HiddenInput,required=False)
    public = forms.BooleanField(help_text='Make the entry public', required=False)
    type=forms.CharField(widget=forms.HiddenInput,required=False)
    tags = TagField(required=False)

    def clean(self):
        if self.data['draft']!='1':
            return super(SSRForm, self).clean()
        else:
            self._errors.clear()
        return self.cleaned_data

    class Meta:
        model=SSR


class WorkspaceInvitationForm(forms.Form):
    invited_users=forms.ModelMultipleChoiceField(queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'width':'250px'}))
    invitation_body=forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=True)


class WorkspaceForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50',
                                                          'onkeyup':"checkWorkspaceTitle(document.getElementById('id_title').value);"}),
        required=True)
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}), required=True)

    class Meta:
        model=Workspace
        exclude=('created_by', 'admin_users','group','related_models','related_bops','related_seds', 'related_ssrs',
                 'forum', 'saved_coordinate_selections')


class WorkspaceBookmarkForm(forms.ModelForm):
    workspace = forms.ModelChoiceField(queryset=Workspace.objects.all(),widget=forms.HiddenInput,required=False)
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)

    class Meta:
        model=WorkspaceBookmark

WorkspaceBookmarkFormSet = inlineformset_factory(Workspace,WorkspaceBookmark,form=WorkspaceBookmarkForm,
    fk_name='workspace',can_delete=True,extra=1)