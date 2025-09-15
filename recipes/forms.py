from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import ModelForm, inlineformset_factory
from .models import Recipe, Ingredient, Step

class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password1 = forms.CharField(
        label="Password",
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'})
    )
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")


class RecipeForm(ModelForm):
    class Meta:
        model = Recipe
        fields = ['name', 'preparation_time', 'min_portion', 'max_portion']
IngredientFormSet = inlineformset_factory(Recipe, Ingredient, fields=('name',), extra=3, can_delete=True)
StepFormSet = inlineformset_factory(Recipe, Step, fields=('order', 'description'), extra=3, can_delete=True)