from django import forms
from django.forms.models import modelformset_factory
from bodb.models import LiteratureAuthor, Journal, Book, Chapter, Conference, Thesis, Unpublished, Author
from registration.models import User

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

