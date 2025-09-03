from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import pytz

# Configuración para la zona horaria de Colombia (UTC-5)
COLOMBIA_TIMEZONE = pytz.timezone('America/Bogota')

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Comida', 'Comida'),
        ('Ropa', 'Ropa'),
        ('Tecnología', 'Tecnología'),
        ('Libros', 'Libros'),
        ('Otros', 'Otros'),
    ]
    
    CONDITION_CHOICES = [
        ('Nuevo', 'Nuevo'),
        ('Usado', 'Usado'),
        ('Buen estado', 'Buen estado'),
    ]
    
    FOOD_TYPE_CHOICES = [
        ('Panadería', 'Panadería'),
        ('Galletas', 'Galletas'),
        ('Repostería', 'Repostería'),
        ('Frutas', 'Frutas'),
        ('Frituras', 'Frituras'),
        ('Dulces', 'Dulces'),
        ('Helados', 'Helados'),
        ('Snacks', 'Snacks'),
        ('Comida rápida', 'Comida rápida'),
        ('Otros', 'Otros'),
    ]

    name = models.CharField(
        max_length=255,
        verbose_name='Nombre',
        help_text='Nombre del producto'
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name='Categoría',
        null=True,
        blank=True
    )
    food_type = models.CharField(
        max_length=50,
        choices=FOOD_TYPE_CHOICES,
        verbose_name='Tipo de Comida',
        blank=True,
        null=True
    )
    description = models.TextField(
        verbose_name='Descripción',
        help_text='Describe tu producto detalladamente'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Precio',
        help_text='Precio en pesos colombianos'
    )
    published_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de publicación'
    )
    condition = models.CharField(
        max_length=50,
        choices=CONDITION_CHOICES,
        verbose_name='Estado',
        blank=True,
        null=True
    )
    image = models.ImageField(
        upload_to='products/',
        verbose_name='Imagen',
        help_text='Imagen del producto'
    )
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Vendedor',
        related_name='products'
    )
    available = models.BooleanField(
        default=True,
        verbose_name='Disponible'
    )

    def clean(self):
        # Actualizar la lógica de validación
        if self.category == 'Comida':
            self.condition = None  # No aplica estado para comida
        else:
            self.food_type = None  # No aplica tipo de comida para otras categorías

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.get_category_display()}"

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['available']),
        ]

    @property
    def average_rating(self):
        comments = self.comments.all()
        if not comments:
            return 0
        return round(sum(comment.rating for comment in comments) / len(comments), 1)

    @property
    def total_ratings(self):
        return self.comments.count()

class Comment(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        max_length=500,
        verbose_name='Comentario'
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name='Calificación',
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='Calificación de 0 a 5 estrellas'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de publicación'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'

    def __str__(self):
        return f'Comentario de {self.user.username} en {self.product.name}'

    def save(self, *args, **kwargs):
        # Si es un nuevo comentario, asignar la fecha actual con la zona horaria de Colombia
        if not self.pk:
            # Obtener la fecha actual en UTC
            now_utc = timezone.now()
            # Convertir a la zona horaria de Colombia
            self.created_at = now_utc.astimezone(COLOMBIA_TIMEZONE)
        super().save(*args, **kwargs)

class Favorite(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de agregado'
    )

    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'

    def __str__(self):
        return f'{self.user.username} ♥ {self.product.name}'

class ChatQuery(models.Model):
    query = models.TextField(
        verbose_name='Consulta',
        help_text='Consulta en lenguaje natural del usuario'
    )
    processed_keywords = models.TextField(
        verbose_name='Palabras clave procesadas',
        help_text='Palabras clave extraídas por Gemini API',
        blank=True,
        null=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_queries'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de consulta'
    )
    success = models.BooleanField(
        default=True,
        verbose_name='Procesamiento exitoso'
    )

    class Meta:
        verbose_name = 'Consulta de chatbot'
        verbose_name_plural = 'Consultas de chatbot'
        ordering = ['-created_at']

    def __str__(self):
        return f"Consulta: {self.query[:50]}..."