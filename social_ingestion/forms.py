from django import forms


class ConnectXForm(forms.Form):
    """Formulario para conectar la cuenta de X/Twitter del usuario"""
    username = forms.CharField(
        label="Usuario de X",
        help_text="Ingresa tu usuario sin @",
        max_length=255,
    )


class UserInterestForm(forms.Form):
    """Formulario para que usuarios expresen sus intereses"""
    text = forms.CharField(
        label="¿Qué te interesa?",
        help_text="Escribe como en X: 'me gustan las manzanas', 'busco libros de ciencia', etc.",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Ej: me gustan las manzanas, busco libros de ciencia, necesito ropa deportiva...',
            'class': 'form-control'
        }),
        max_length=500,
    )


