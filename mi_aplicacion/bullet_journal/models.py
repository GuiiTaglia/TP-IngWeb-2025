from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json
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
    
    # Campo para almacenar datos de hábitos personalizados en formato JSON
    custom_habits_data = models.JSONField(default=dict, blank=True)
    def __str__(self):
        return f"{self.date} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        """Override save para sincronizar con HabitTracking"""
        super().save(*args, **kwargs)
        
        # Sincronizar hábitos personalizados con HabitTracking
    #    self.sync_custom_habits()

    # def sync_custom_habits(self):
    #     """Sincroniza los datos de hábitos personalizados con la tabla HabitTracking"""
    #     if not self.custom_habits_data:
    #         return
        
    #     for habit_id_str, value in self.custom_habits_data.items():
    #         try:
    #             habit_id = int(habit_id_str.replace('habit_', ''))
    #             habit = CustomHabit.objects.get(id=habit_id, user=self.user)
                
    #             # Crear o actualizar el registro en HabitTracking
    #             tracking, created = HabitTracking.objects.get_or_create(
    #                 habit=habit,
    #                 date=self.date
    #             )
                
    #             # Actualizar el valor según el tipo de hábito
    #             if habit.type == 'boolean':
    #                 tracking.boolean_value = value if value is not None else False
    #             elif habit.type == 'integer':
    #                 tracking.integer_value = value if value is not None else 0
    #             elif habit.type == 'float':
    #                 tracking.float_value = value if value is not None else 0.0
                
    #             tracking.save()
                
    #         except (ValueError, CustomHabit.DoesNotExist):
    #             continue   

    def get_custom_habits_for_date(self):
        """Obtiene los hábitos personalizados para esta fecha específica"""
    
        return self.custom_habits_data or {}
    
    
    
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
        
        for habit in custom_habits:
            field_name = f'habit_{habit.id}'
        
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
                'color': '#2ecc71',  # Color por defecto para hábitos
                'chart_type': 'bar' if habit.type == 'boolean' else 'line',
                'data': data
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
    
class HabitTracking(models.Model):
    habit = models.ForeignKey(CustomHabit, on_delete=models.CASCADE, related_name='tracking_entries')
    date = models.DateField()
    boolean_value = models.BooleanField(null=True, blank=True)
    integer_value = models.IntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.habit.name} - {self.date}"
    
    def get_value(self):
        if self.habit.type == 'boolean':
            return self.boolean_value
        elif self.habit.type == 'integer':
            return self.integer_value
        elif self.habit.type == 'float':
            return self.float_value
        return None
