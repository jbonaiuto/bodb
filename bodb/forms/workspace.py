from django import forms
from django.forms.models import inlineformset_factory
from bodb.models import Workspace, WorkspaceBookmark
from registration.models import User

class WorkspaceUserForm(forms.ModelForm):
    class Meta:
        model = User
        exclude=('last_login', 'date_joined', 'password', 'groups','username')


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
                 'related_regions', 'related_literature', 'forum', 'saved_coordinate_selections')


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