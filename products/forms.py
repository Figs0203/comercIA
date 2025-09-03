from django import forms
from .models import Product, Comment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'food_type', 'description', 'price',
            'condition', 'image', 'available'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control', 'id': 'id_category'}),
            'food_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_food_type'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe tu producto detalladamente'
            }),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-control', 'id': 'id_condition'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'available': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['food_type'].required = False
        self.fields['condition'].required = False
        
        # Configuración específica para el campo available
        self.fields['available'].label = 'Producto disponible'
        self.fields['available'].help_text = 'Desmarque esta opción si el producto no está disponible temporalmente'
        
        # Si es una instancia nueva (creación), excluimos el campo available
        if not kwargs.get('instance'):
            del self.fields['available']
        
        # Mejora de las etiquetas y mensajes de ayuda
        for field in self.fields:
            if self.fields[field].required:
                self.fields[field].label = f"{self.fields[field].label} *"

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        
        if category == 'Comida':
            food_type = cleaned_data.get('food_type')
            if not food_type:
                self.add_error('food_type', 'Debe seleccionar un tipo de comida')
            cleaned_data['condition'] = None
        else:
            condition = cleaned_data.get('condition')
            if not condition:
                self.add_error('condition', 'Debe seleccionar un estado para el producto')
            cleaned_data['food_type'] = None
        
        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Escribe tu comentario aquí...',
                'class': 'comment-input'
            }),
            'rating': forms.HiddenInput(attrs={
                'class': 'rating-input'
            })
        }

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if not text.strip():
            raise forms.ValidationError('El comentario no puede estar vacío')
        if len(text) > 500:
            raise forms.ValidationError('El comentario no puede tener más de 500 caracteres')
        return text

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None:
            raise forms.ValidationError('Debes asignar una calificación')
        if not (0 <= rating <= 5):
            raise forms.ValidationError('La calificación debe estar entre 0 y 5')
        return rating

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.'
        self.fields['password1'].help_text = '''
            <ul>
                <li>Tu contraseña no puede ser muy similar a tu otra información personal.</li>
                <li>Tu contraseña debe contener al menos 8 caracteres.</li>
                <li>Tu contraseña no puede ser una contraseña comúnmente utilizada.</li>
                <li>Tu contraseña no puede ser completamente numérica.</li>
            </ul>
        '''
        self.fields['password2'].help_text = 'Ingresa la misma contraseña que antes, para verificación.' 