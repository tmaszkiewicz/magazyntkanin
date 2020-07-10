from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

class LoginForm(forms.Form):
        user = forms.CharField(label='LOGIN')
        password = forms.CharField(label='HASŁO', widget=forms.PasswordInput)
