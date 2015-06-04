from django.forms import Form
from django import forms
from django.forms.models import modelformset_factory, inlineformset_factory
from bodb.forms.document import DocumentWithLiteratureForm, DocumentForm
from bodb.models import ModelAuthor, Model, Module, Author, Variable, Document, RelatedModel, Literature
from registration.models import User
from taggit.forms import TagField


class ModelForm(DocumentWithLiteratureForm):
    authors = forms.ModelMultipleChoiceField(queryset=ModelAuthor.objects.order_by('order'),
        widget=forms.MultipleHiddenInput, required=False)
    execution_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    documentation_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    description_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    simulation_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    modeldb_accession_number = forms.IntegerField(widget=forms.TextInput(attrs={'size':'10'}),required=False)

    class Meta:
        model = Model

class ModelForm1(Form):
    collator = forms.ModelChoiceField(queryset=User.objects.all(),widget=forms.HiddenInput,required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'50'}),required=True)
    authors = forms.ModelMultipleChoiceField(queryset=ModelAuthor.objects.order_by('order'),
        widget=forms.MultipleHiddenInput, required=False)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'3'}),required=True)
    tags = TagField(required=False)
    public = forms.BooleanField(help_text='Make the entry public', required=False)
    execution_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    documentation_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    description_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    simulation_url = forms.URLField(widget=forms.TextInput(attrs={'size':'50'}),required=False)
    modeldb_accession_number = forms.IntegerField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    literature = forms.ModelMultipleChoiceField(queryset=Literature.objects.order_by('title'),
        widget=forms.MultipleHiddenInput, required=False)

class ModelForm2(Form):
    narrative = forms.CharField(widget=forms.Textarea(attrs={'cols':'57','rows':'5'}),required=False)

class ModelForm6(Form):
    draft=forms.CharField(widget=forms.HiddenInput,required=False)

class ModuleForm(DocumentForm):
    parent = forms.ModelChoiceField(queryset=Module.objects.all(), required=True)

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


ModelAuthorFormSet = lambda *a, **kw: modelformset_factory(ModelAuthor,form=ModelAuthorInlineForm, exclude=('author',),
    extra=kw.pop('extra', 0), can_delete=True)(*a, **kw)

class VariableInlineForm(forms.ModelForm):
    module = forms.ModelChoiceField(queryset=Module.objects.all(),widget=forms.HiddenInput,required=False)
    name = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=True)
    data_type = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}),required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'cols':'42','rows':'3'}),required=False)
    var_type = forms.CharField(widget=forms.HiddenInput,required=True)
    class Meta:
        model=Variable


VariableFormSet = lambda *a, **kw: inlineformset_factory(Module,Variable,form=VariableInlineForm, fk_name='module',
    extra=kw.pop('extra', 0), can_delete=True)(*a, **kw)


class ModuleInlineForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'size':'13'}),required=True)
    brief_description = forms.CharField(widget=forms.Textarea(attrs={'cols':'47','rows':'3'}),required=False)

    class Meta:
        model = Module
        exclude=('tags','collator','draft','public')


ModuleFormSet = lambda *a, **kw: inlineformset_factory(Module,Module,form=ModuleInlineForm, fk_name='parent',
    extra=kw.pop('extra', 0), can_delete=True)(*a, **kw)


class RelatedModelInlineForm(forms.ModelForm):
    document = forms.ModelChoiceField(queryset=Document.objects.all(),widget=forms.HiddenInput,required=False)
    relationship = forms.CharField(widget=forms.Textarea(attrs={'cols':'40','rows':'3'}),required=False)
    model = forms.ModelChoiceField(queryset=Model.objects.all(),widget=forms.HiddenInput,required=False)

    class Meta:
        model=RelatedModel


RelatedModelFormSet = lambda *a, **kw: inlineformset_factory(Document,RelatedModel,form=RelatedModelInlineForm, fk_name='document',
    extra=kw.pop('extra', 0), can_delete=True)(*a, **kw)


class ModelReportForm(Form):
    format=forms.ChoiceField(choices=[('rtf','RTF'),('pdf','PDF')],required=True, help_text='File format to export')
    figure_display=forms.BooleanField(required=False, help_text='Display figures in report')
    narrative_display=forms.BooleanField(required=False, help_text='Display narrative in report')
    summary_display=forms.BooleanField(required=False, help_text='Display SEDs, SSRs and Predictions in report')
    url_display=forms.BooleanField(required=False, help_text='Display URLs in report')
    related_model_display=forms.BooleanField(required=False, help_text='Display related models in report')
    related_bop_display=forms.BooleanField(required=False, help_text='Display related BOPs in report')
    related_brainregion_display=forms.BooleanField(required=False, help_text='Display related brain regions in report')
    reference_display=forms.BooleanField(required=False, help_text='Display references in report')
    include_seds=forms.BooleanField(required=False, help_text='Include SED reports in report')


class ModuleReportForm(Form):
    format=forms.ChoiceField(choices=[('rtf','RTF'),('pdf','PDF')],required=True, help_text='File format to export')
    figure_display=forms.BooleanField(required=False, help_text='Display figures in report')
    narrative_display=forms.BooleanField(required=False, help_text='Display narrative in report')
