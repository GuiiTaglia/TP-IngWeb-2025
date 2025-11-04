from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json
from django.urls import reverse
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
    
    title = models.CharField(max_length=200, blank=True, null=True)  
    diary_entry = models.TextField(blank=True, null=True)  
    diary_image = models.ImageField(upload_to='diary_images/', null=True, blank=True)  

    # Campo para almacenar datos de hábitos personalizados en formato JSON
    custom_habits_data = models.JSONField(default=dict, blank=True)
    def __str__(self):
        return f"{self.date} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        """Override save para sincronizar con HabitTracking"""
        super().save(*args, **kwargs)
        

    def get_custom_habits_for_date(self):
        """Obtiene los hábitos personalizados para esta fecha específica"""
    
        return self.custom_habits_data or {}

    def get_custom_habits_text(self):
        if not self.custom_habits_data:
            return ""
        parts = []
        for k, v in self.custom_habits_data.items():
            try:
                parts.append(str(v))
            except Exception:
                continue
        return " ".join(parts)
    
    def get_absolute_url(self):
        return reverse('journal_detail', args=[str(self.pk)])
    
    
    
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
        current_date = start_date
        while current_date <= end_date:
            data[current_date] = None
            current_date += timedelta(days=1)

        #llenar con datos reales 
        for entry in entries:
            if hasattr(entry, field_name):
                # Campo estándar del Journal
                data[entry.date] = getattr(entry, field_name)
            elif field_name.startswith('habit_'):
                # Hábito personalizado desde custom_habits_data
                habit_value = entry.custom_habits_data.get(field_name)
                data[entry.date] = habit_value
            
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
            if hasattr(entry, field_name):
                # Campo estándar del Journal
                data[entry.date] = getattr(entry, field_name)
            elif field_name.startswith('habit_'):
                # Hábito personalizado
                habit_value = entry.custom_habits_data.get(field_name)
                data[entry.date] = habit_value

        return {
            'labels': [date.strftime('%d/%m') for date in data.keys()],
            'values': list(data.values())
        }
    
    @classmethod 
    def get_all_stats_for_user(cls, user, period='weekly'):
        """Método unificado para obtener estadísticas de Journal + hábitos personalizados"""
        stats = []
        
            # Configuración de campos básicos del Journal
        basic_fields_config = {
            'water_glasses': {
            'name': 'Vasos de Agua',
            'color': '#3498db',
            'chart_type': 'bar'
            },
            'sleep_hours': {
                'name': 'Horas de Sueño',
                'color': '#9b59b6',
                'chart_type': 'line'
            },
            'exercise': {
                'name': 'Ejercicio',
                'color': '#e74c3c',
                'chart_type': 'bar'
            },
            'mood': {
                'name': 'Estado de Ánimo',
                'color': '#f39c12',
                'chart_type': 'pie'
            }   
    }
        
        for field, config in basic_fields_config.items():
            if period == 'weekly':
                data = cls.get_weekly_data(user, field)
            elif period == 'monthly':
                data = cls.get_monthly_data(user, field)
            else: 
                data = cls.get_weekly_data(user, field)  # Por defecto semanal
            
            stats.append({
                'id': f'journal_{field}',
                'field': field,
                'field_display': config['name'],
                'type': 'boolean' if field == 'exercise' else 'numeric',
                'color': config['color'],
                'chart_type': config['chart_type'],
                'data': data
            })
        
        # Estadísticas de hábitos personalizados
        custom_habits = CustomHabit.objects.filter(user=user, is_active=True)
        
        
            
        habit_colors = [
            '#e74c3c',  # Rojo
            '#3498db',  # Azul
            '#2ecc71',  # Verde
            '#f39c12',  # Naranja
            '#9b59b6',  # Morado
            '#1abc9c',  # Turquesa
            '#e67e22',  # Naranja oscuro
            '#34495e',  # Gris azulado
            '#f1c40f',  # Amarillo
            '#e91e63',  # Rosa
            '#795548',  # Marrón
            '#607d8b'   # Gris
        ]

        for index, habit in enumerate(custom_habits):
            field_name = f'habit_{habit.id}'
            color = habit_colors[index % len(habit_colors)]

            # Obtener datos desde custom_habits_data del Journal (no desde HabitTracking)
            if period == 'weekly':
                data = cls.get_weekly_data(user, field_name)
            elif period == 'monthly':
                data = cls.get_monthly_data(user, field_name)
            else:
                data = cls.get_weekly_data(user, field_name)
            
            stats.append({
                'id': f'habit_{habit.id}',
                'field': field_name,
                'field_display': habit.name,
                'type': habit.type,
                'color': color,
                'chart_type': 'bar' if habit.type == 'boolean' else 'line',
                'data': data,
                'goal_value': habit.goal_value,
                'unit': habit.unit,
                'habit_type': habit.type
            })
    
        return stats

    class Meta:
        unique_together = ('user', 'date')

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
        ##('float', 'Número Decimal'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_habits')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    #Campos para metas
    goal_value = models.IntegerField(null=True, blank=True)  # Valor objetivo (si aplica)
    unit = models.CharField(max_length=20, blank=True, null=True)  #
    #opcionales para personalizacion 
       
    #icon = models.CharField(max_length=50, blank=True, null=True)  # Para iconos de FontAwesome o similares
    #color = models.CharField(max_length=20, default='#3498db')     # Color para gráficos
    #goal_value = models.FloatField(null=True, blank=True)          # Valor objetivo (si aplica)
    #unit = models.CharField(max_length=20, blank=True, null=True)  # Unidad (ej: "km", "páginas", etc.)
    class Meta:
        unique_together = ('user', 'name')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    # Métodos para estadísticas de hábitos personalizados
    def get_weekly_tracking(self, end_date=None):
        """Obtiene datos de seguimiento semanal para este hábito"""
        if not end_date:
            end_date = timezone.now().date()
        start_date = end_date - timedelta(days=6)
        
        tracking = self.tracking_entries.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        data = {}
        current_date = start_date
        while current_date <= end_date:
            data[current_date] = None
            current_date += timedelta(days=1)
        
        for entry in tracking:
            if self.type == 'boolean':
                data[entry.date] = entry.boolean_value
            elif self.type == 'integer':
                data[entry.date] = entry.integer_value
            elif self.type == 'float':
                data[entry.date] = entry.float_value
            
        return {
            'labels': [date.strftime('%d/%m') for date in data.keys()],
            'values': list(data.values())
        }
    
    @classmethod
    def get_monthly_tracking(cls, user, habit_id, year=None, month=None):
        """Obtiene datos de seguimiento mensual para un hábito específico"""
        from calendar import monthrange

        if year is None or month is None:
            now = timezone.now()
            year = now.year
            month = now.month

        _, last_day = monthrange(year, month)
        start_date = timezone.datetime(year, month, 1).date()
        end_date = timezone.datetime(year, month, last_day).date()

        try:
            habit = cls.objects.get(id=habit_id, user=user)
        except cls.DoesNotExist:
            return None

        tracking = habit.tracking_entries.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        data = {}
        current_date = start_date
        while current_date <= end_date:
            data[current_date] = None
            current_date += timedelta(days=1)

        for entry in tracking:
            if habit.type == 'boolean':
                data[entry.date] = entry.boolean_value
            elif habit.type == 'integer':
                data[entry.date] = entry.integer_value
            elif habit.type == 'float':
                data[entry.date] = entry.float_value

        return {
            'labels': [date.strftime('%d/%m') for date in data.keys()],
            'values': list(data.values())
        }
    
    



