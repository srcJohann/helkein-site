from allauth.account.forms import LoginForm
from django import forms

class CustomLoginForm(LoginForm):
    def clean(self):
        try:
            return super().clean()
        except forms.ValidationError:
            raise forms.ValidationError("Seu e-mail ou senha estão errados, tente novamente")
