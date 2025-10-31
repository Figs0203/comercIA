from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import re
import urllib.parse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
import pytz

# Configuración para la zona horaria de Colombia (UTC-5)
COLOMBIA_TIMEZONE = pytz.timezone('America/Bogota')

class SellerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='seller_profile'
    )
    profile_image = models.ImageField(
        upload_to='profiles/',
        verbose_name=_('Foto de perfil'),
        null=True,
        blank=True
    )
    store_name = models.CharField(
        max_length=100,
        verbose_name=_('Nombre de la tienda'),
        help_text=_('Nombre que se mostrará en tu perfil de vendedor')
    )
    slogan = models.CharField(
        max_length=200,
        verbose_name=_('Slogan'),
        help_text=_('Una frase corta que describa tu tienda'),
        blank=True,
        null=True
    )
    slogan_en = models.CharField(
        max_length=200,
        verbose_name=_('Slogan (English)'),
        help_text=_('English version of your store slogan'),
        blank=True,
        null=True
    )
    description = models.TextField(
        verbose_name=_('Descripción'),
        help_text=_('Describe tu tienda y los productos que vendes')
    )
    description_en = models.TextField(
        verbose_name=_('Descripción (English)'),
        help_text=_('Describe your store and products (English)'),
        blank=True,
        null=True
    )
    whatsapp = models.CharField(
        max_length=15,
        verbose_name=_('WhatsApp'),
        help_text=_('Ingresa tu número de WhatsApp con código de país (ej: 573001234567)'),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Perfil de vendedor'
        verbose_name_plural = 'Perfiles de vendedores'

    def __str__(self):
        return f"Tienda de {self.store_name}"

    def clean(self):
        super().clean()
        if self.whatsapp:
            # Eliminar cualquier espacio o carácter especial
            self.whatsapp = re.sub(r'[^0-9]', '', self.whatsapp)
            
            # Verificar formato
            if not re.match(r'^57[3]\d{9}$', self.whatsapp):
                raise ValidationError({
                    'whatsapp': 'El número debe comenzar con 57 seguido de un 3 y 9 dígitos más.'
                })

    def get_whatsapp_link(self, product_name=None):
        if not self.whatsapp:
            return None
        
        base_url = f"https://wa.me/{self.whatsapp}"
        if product_name:
            message = f"Hola, estoy interesado en el producto: {product_name}. ¿Podrías darme más información?"
            return f"{base_url}?text={urllib.parse.quote(message)}"
        return base_url

class Schedule(models.Model):
    DAYS_OF_WEEK = [
        ('Lunes', _('Lunes')),
        ('Martes', _('Martes')),
        ('Miércoles', _('Miércoles')),
        ('Jueves', _('Jueves')),
        ('Viernes', _('Viernes'))
    ]

    profile = models.ForeignKey(
        SellerProfile,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    day = models.CharField(
        max_length=20,
        choices=DAYS_OF_WEEK,
        verbose_name=_('Día')
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name=_('Disponible')
    )
    start_time = models.TimeField(
        verbose_name=_('Hora de inicio'),
        null=True,
        blank=True,
        help_text=_('Horario de inicio (entre 6:00 AM y 9:30 PM, en intervalos de 30 minutos)')
    )
    end_time = models.TimeField(
        verbose_name=_('Hora de cierre'),
        null=True,
        blank=True,
        help_text=_('Horario de cierre (entre 6:30 AM y 10:00 PM, en intervalos de 30 minutos)')
    )

    class Meta:
        ordering = ['day']
        unique_together = ['profile', 'day']
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'

    def clean(self):
        super().clean()
        
        if self.is_available:
            if not self.start_time or not self.end_time:
                raise ValidationError({
                    'start_time': 'Debe especificar hora de inicio cuando el día está disponible',
                    'end_time': 'Debe especificar hora de cierre cuando el día está disponible'
                })
            
            # Convertir a minutos para comparaciones más fáciles
            start_time_minutes = self.start_time.hour * 60 + self.start_time.minute
            end_time_minutes = self.end_time.hour * 60 + self.end_time.minute
            
            # Validar rango de horas (6:00 AM a 10:00 PM)
            if start_time_minutes < 6 * 60 or start_time_minutes >= 22 * 60:
                raise ValidationError({
                    'start_time': 'La hora de inicio debe estar entre las 6:00 AM y las 9:30 PM'
                })
            if end_time_minutes < (6 * 60 + 30) or end_time_minutes > 22 * 60:
                raise ValidationError({
                    'end_time': 'La hora de cierre debe estar entre las 6:30 AM y las 10:00 PM'
                })
            
            # Validar que la hora de inicio sea anterior a la de cierre
            if start_time_minutes >= end_time_minutes:
                raise ValidationError({
                    'end_time': 'La hora de cierre debe ser posterior a la hora de inicio'
                })

            # Validar intervalos de 30 minutos
            if start_time_minutes % 30 != 0 or end_time_minutes % 30 != 0:
                raise ValidationError({
                    'start_time': 'Las horas deben ser en intervalos de 30 minutos (ejemplo: 6:00, 6:30, 7:00, etc.)',
                    'end_time': 'Las horas deben ser en intervalos de 30 minutos (ejemplo: 6:00, 6:30, 7:00, etc.)'
                })

            # Validar que haya al menos 30 minutos entre inicio y cierre
            if end_time_minutes - start_time_minutes < 30:
                raise ValidationError({
                    'end_time': 'Debe haber al menos 30 minutos entre la hora de inicio y cierre'
                })
        else:
            self.start_time = None
            self.end_time = None

    def __str__(self):
        if not self.is_available:
            return f"{self.day}: No disponible"
        return f"{self.day}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    

class ProfileClick(models.Model):
    profile = models.ForeignKey(
        SellerProfile,
        on_delete=models.CASCADE,
        related_name='clicks'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,  # Puede ser anónimo
        blank=True
    )
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"Clic en {self.profile.store_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"