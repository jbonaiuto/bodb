from django import forms
from django.contrib.auth.models import Group
from bodb.models import BodbProfile, BrainRegionRequest
from registration.forms import RegistrationForm
from registration.models import User
from uscbp.widgets import ImageWidget
from django.core.cache import cache

class UserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.order_by('name'),
        widget=forms.SelectMultiple(attrs={'size':'5'}),
        help_text='Hold down "Control", or "Command" on a Mac, to select more than one.',
        required=False)
    class Meta:
        model = User
        exclude=('last_login', 'date_joined', 'password')


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

        cache.set('%d.profile' % new_user.id, profile)

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
        exclude=('active_workspace','loaded_coordinate_selection','favorites', 'favorite_literature', 'favorite_regions')


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