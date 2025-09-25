from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
#from cloudinary_storage.storage import RawMediaCloudinaryStorage  deje esto aca por si usamos pdf en algun momento

class Journal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    mood = models.CharField(max_length=50)
    sleep_hours = models.FloatField(null=True)
    water_glasses = models.IntegerField(null=True)
    exercise = models.BooleanField(default=False)
    image = models.ImageField(upload_to='journal_images/', null=True, blank=True)
    #esto solo si queremos pdf --> pruebas_en_pdf = models.FileField(upload_to='raw/', blank=True) Adicionalmente, si necesitamos manejar archivos PDF o ZIP debemos habilitar la opción de CLoudinary que permite esto en la pestaña Seguiridad
    # y esto por si queremos video: video = models.FileField(upload_to='videos/noticias',blank=True)

    def __str__(self):
        return f"{self.date} - {self.user.username}"
    
#Metodos de clase para consultas estadisticas
    @classmethod
    def get_weekly_data(cls, user, field_name, end_date=None):
        if not end_date:
            end_date = timezone.now().date()
        start_date = end_date - timedelta(days=6)

        entries = cls.objects.filter(
            user=user, 
            date__gte=(start_date),
            date__lte=end_date
            ).order_by('date')
        
        #crear diccionario con fechas y valores
        data = {}
        currente_date = start_date
        while currente_date <= end_date:
            data[currente_date] = None
            currente_date += timedelta(days=1)

        #llenar con datos reales 
        for entry in entries:
            data[entry.date] = getattr(entry, field_name)

        return {
            'labels': [date.strftime('%d/%m') for date in data.keys()],
            'values': list(data.values())
        }
    
    @classmethod
    def get_monthly_data(cls, user, field_name, year=None, month=None):
        from calendar import monthrange

        if year is None or month is None:
            now = timezone.now()
            year = now.year
            month = now.month

        _, last_day = monthrange(year, month)
        start_date = timezone.datetime(year, month, 1).date()
        end_date = timezone.datetime(year, month, last_day).date()

        entries = cls.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        #Crear diccionario con fechas y valores 
        data = {}
        current_date = start_date
        while current_date <= end_date:
            data[current_date] = None
            current_date += timedelta(days=1)

        #llenar con datos reales
        for entry in entries:
            data[entry.date] = getattr(entry, field_name)

        return {
            'labels': [date.strftime('%d/%m') for date in data.keys()],
            'values': list(data.values())
        }
    
#si queremos que el usuario elija que estadisticas ver: 
class StatsPreference(models.Model):
    PERIOD_CHOICES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('yearly', 'Anual'),
    ]

    FIELD_CHOICES = [
        ('mood', 'Estado de ánimo'),
        ('sleep_hours', 'Horas de sueño'),
        ('water_glasses', 'Vasos de agua'),
        ('exercise', 'Ejercicio'),
    ]

    CHART_TYPE_CHOICES = [
        ('line', 'Línea'),
        ('bar', 'Barra'),
        ('pie', 'Pastel'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    field = models.CharField(max_length=50, choices=FIELD_CHOICES)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='weekly')
    chart_type = models.CharField(max_length=10, choices=CHART_TYPE_CHOICES, default='line')
    is_visible = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'field')
        ordering = ['display_order']
        
    def __str__(self):
        return f"{self.user.username} - {self.get_field_display()} ({self.get_period_display()})"
    

class CustomHabit(models.Model):
    TYPE_CHOICES = [
        ('boolean', 'Sí/No'),
        ('integer', 'Número'),
        ('float', 'Número Decimal'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_habits')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    #opcionales para personalizacion 
       
    #icon = models.CharField(max_length=50, blank=True, null=True)  # Para iconos de FontAwesome o similares
    #color = models.CharField(max_length=20, default='#3498db')     # Color para gráficos
    #goal_value = models.FloatField(null=True, blank=True)          # Valor objetivo (si aplica)
    #unit = models.CharField(max_length=20, blank=True, null=True)  # Unidad (ej: "km", "páginas", etc.)
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"