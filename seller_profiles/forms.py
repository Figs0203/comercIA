from django import forms
from .models import SellerProfile, Schedule
from django.forms import inlineformset_factory
import re

class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ['profile_image', 'store_name', 'slogan', 'description', 'whatsapp']
        widgets = {
            'store_name': forms.TextInput(attrs={'class': 'form-control'}),
            'slogan': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '573001234567'
            }),
        }
        help_texts = {
            'store_name': 'Nombre visible de tu negocio para los compradores.',
            'slogan': 'Una frase corta que describa tu negocio (opcional).',
            'description': 'Describe tu negocio, qué productos vendes y cualquier información relevante para tus clientes.',
            'profile_image': 'Sube una imagen de tu logo o perfil (opcional).',
            'whatsapp': 'Número de WhatsApp para contacto (opcional). Formato: 573001234567.'
        }
        error_messages = {
            'store_name': {
                'required': 'Por favor ingresa un nombre para tu tienda.',
                'max_length': 'El nombre de la tienda no puede exceder los 100 caracteres.'
            },
            'description': {
                'required': 'Por favor ingresa una descripción para tu tienda.'
            }
        }

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp')
        if whatsapp:
            # Eliminar cualquier espacio o carácter especial
            whatsapp = re.sub(r'[^0-9]', '', whatsapp)
            
            # Verificar que el número tenga el formato correcto
            if not re.match(r'^57[3]\d{9}$', whatsapp):
                raise forms.ValidationError(
                    'El número debe comenzar con 57 seguido de un 3 y 9 dígitos más. Ejemplo: 573001234567'
                )
            
            return whatsapp
        return None

class ScheduleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generar opciones de tiempo en intervalos de 30 minutos
        start_time_choices = []
        end_time_choices = []
        
        for hour in range(6, 22):  # 6 AM a 9:30 PM para inicio, 6:30 AM a 10 PM para cierre
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                time_display = f"{hour:02d}:{minute:02d}"
                
                if hour < 22 or (hour == 21 and minute == 30):  # Solo hasta 9:30 PM para inicio
                    start_time_choices.append((time_str, time_display))
                if (hour > 6 or (hour == 6 and minute == 30)) and (hour < 22 or minute == 0):  # 6:30 AM a 10 PM para cierre
                    end_time_choices.append((time_str, time_display))
        
        self.fields['start_time'].widget = forms.Select(choices=[('', 'Seleccionar hora')] + start_time_choices)
        self.fields['end_time'].widget = forms.Select(choices=[('', 'Seleccionar hora')] + end_time_choices)
        
        self.fields['start_time'].widget.attrs.update({'class': 'form-select time-select'})
        self.fields['end_time'].widget.attrs.update({'class': 'form-select time-select'})

    class Meta:
        model = Schedule
        fields = ['day', 'is_available', 'start_time', 'end_time']
        widgets = {
            'day': forms.HiddenInput(),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input availability-toggle',
                'role': 'switch'
            }),'start_time': forms.Select(attrs={
                'class': 'form-select time-select',
            }),
            'end_time': forms.Select(attrs={
                'class': 'form-select time-select',
                'min': '06:30',  # Mínimo 30 minutos después de la hora de inicio mínima
                'max': '22:00',
                'placeholder': 'Selecciona hora de cierre'
            }),
        }
        help_texts = {
            'is_available': 'Indica si estás disponible este día.',
            'start_time': 'Hora de inicio (entre 6:00 AM y 9:30 PM)',
            'end_time': 'Hora de cierre (entre 6:30 AM y 10:00 PM)'
        }

    def clean(self):
        cleaned_data = super().clean()
        is_available = cleaned_data.get('is_available')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if is_available:
            if not start_time:
                self.add_error('start_time', 'Debes especificar una hora de inicio cuando el día está disponible')
            if not end_time:
                self.add_error('end_time', 'Debes especificar una hora de cierre cuando el día está disponible')

            if start_time and end_time:
                # Verificar que haya al menos 30 minutos entre inicio y cierre
                time_diff = (end_time.hour * 60 + end_time.minute) - (start_time.hour * 60 + start_time.minute)
                if time_diff < 30:
                    self.add_error('end_time', 'Debe haber al menos 30 minutos entre la hora de inicio y cierre')

        return cleaned_data

class ScheduleFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Si es un nuevo perfil
            self.initial = [
                {'day': day[0]} for day in Schedule.DAYS_OF_WEEK
            ]

ScheduleInlineFormSet = inlineformset_factory(
    SellerProfile,
    Schedule,
    formset=ScheduleFormSet,
    form=ScheduleForm,
    extra=0,
    min_num=5,
    max_num=5,
    validate_min=True,
    validate_max=True,
    can_delete=False
)