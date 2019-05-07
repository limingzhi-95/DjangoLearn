from django import forms


class AddForm(forms.Form):
    name = forms.CharField()
    age = forms.IntegerField()
    image = forms.FileField()

