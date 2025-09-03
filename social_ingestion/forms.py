from django import forms


class ConnectXForm(forms.Form):
    username = forms.CharField(
        label="Usuario de X",
        help_text="Ingresa tu usuario sin @",
        max_length=255,
    )


