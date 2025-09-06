from django import forms


class ConnectXForm(forms.Form):
    """Formulario para conectar la cuenta de X/Twitter del usuario"""
    username = forms.CharField(
        label="Usuario de X",
        help_text="Ingresa tu usuario sin @",
        max_length=255,
    )


