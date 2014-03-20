from django import forms
from django.forms.models import ErrorList
from bodb.models import Message
from registration.models import User

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