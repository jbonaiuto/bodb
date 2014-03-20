from django import forms
from django.forms.models import inlineformset_factory
from bodb.models import Subscription, UserSubscription
from registration.models import User

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