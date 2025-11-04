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
    
    # AGREGAR ESTOS CAMPOS NUEVOS:
    title = models.CharField(max_length=200, blank=True, null=True)  # Título del día
    diary_entry = models.TextField(blank=True, null=True)  # Descripción del día
    diary_image = models.ImageField(upload_to='diary_images/', null=True, blank=True)  # Imagen para el diario

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
    
    # En bullet_journal/models.py - MEJORAR el método get_yearly_data con más DEBUG

    @classmethod
    def get_yearly_data(cls, user, field_name):
        """Obtiene datos anuales agrupados por mes"""
        import calendar
        from collections import defaultdict
        from datetime import datetime
        
        print(f"🔍 DEBUG get_yearly_data: ===== INICIANDO para campo {field_name} =====")
        
        entries = cls.objects.filter(user=user).order_by('date')
        print(f"🔍 DEBUG get_yearly_data: Total entries del usuario: {entries.count()}")
        
        for entry in entries[:3]:  # Mostrar primeras 3 entradas
            print(f"  └─ Entry: {entry.date} - exercise: {entry.exercise}, water: {entry.water_glasses}")
            if entry.custom_habits_data:
                print(f"      Hábitos: {entry.custom_habits_data}")
        
        if not entries.exists():
            print(f"❌ DEBUG get_yearly_data: No hay entradas para {field_name}")
            return {'labels': [], 'values': [], 'period': 'yearly'}
        
        # Usar el año más reciente con datos
        years_with_data = entries.dates('date', 'year')
        current_year = datetime.now().year
        
        print(f"🔍 DEBUG get_yearly_data: Años con datos: {[y.year for y in years_with_data]}")
        
        if entries.filter(date__year=current_year).exists():
            target_year = current_year
        else:
            target_year = years_with_data.last().year
        
        print(f"🔍 DEBUG get_yearly_data: Año seleccionado: {target_year} para {field_name}")
        
        # Filtrar entradas del año seleccionado
        yearly_entries = entries.filter(date__year=target_year)
        print(f"🔍 DEBUG get_yearly_data: {yearly_entries.count()} entradas en {target_year}")
        
        monthly_data = defaultdict(list)
        monthly_total_days ={}

        for entry in yearly_entries:
            month_name = calendar.month_name[entry.date.month]
            month_num = entry.date.month
            print(f"🔍 DEBUG: Procesando entrada {entry.date} - mes {month_name}")


            if month_name not in monthly_total_days:
                monthly_total_days[month_name] = set()
            monthly_total_days[month_name].add(entry.date)

            if hasattr(entry, field_name):
                value = getattr(entry, field_name)
                print(f"  └─ Campo estándar {field_name}: {value} (tipo: {type(value)})")
                if value is not None:
                    monthly_data[month_name].append(value)
            elif field_name.startswith('habit_'):
                print(f"  └─ Procesando hábito {field_name}")
                if entry.custom_habits_data:
                    habit_value = entry.custom_habits_data.get(field_name)
                    print(f"      Valor de hábito {field_name}: {habit_value} (tipo: {type(habit_value)})")
                    if habit_value is not None:
                        monthly_data[month_name].append(habit_value)
                else:
                    print(f"      No hay custom_habits_data en entrada {entry.date}")

        print(f"🔍 DEBUG: Datos mensuales recolectados: {dict(monthly_data)}")

        labels = []
        values = []
        days_info = []

        for month_num in range(1, 13):
            month_name = calendar.month_name[month_num]
            month_abbr = month_name[:3]  # Ene, Feb, Mar, etc.
            labels.append(month_abbr)
            
            if month_name in monthly_data and monthly_data[month_name]:
                month_values = monthly_data[month_name]
                total_days_in_month = len(monthly_total_days.get(month_name))
                print(f"🔍 DEBUG: {month_name} tiene valores: {month_values}")

                # Determinar si es boolean
                is_boolean = (field_name == 'exercise' or 
                            (field_name.startswith('habit_') and
                            any(isinstance(v, bool) for v in month_values)))
                
                print(f"  └─ Campo {field_name} es boolean: {is_boolean}")
                
                if is_boolean:

                    if month_name in monthly_total_days:
                        first_date = min(monthly_total_days[month_name])
                        year_for_month = first_date.year
                        total_days_in_month = calendar.monthrange(year_for_month, month_num)[1]

                        days_completed = sum(1 for v in month_values if v is True)

                        percentage = round((days_completed / total_days_in_month) * 100, 1)
                    
                        values.append(percentage)
                        days_info.append(f"{days_completed}/{total_days_in_month}")

                        print(f"  └─ Boolean: {days_completed}/{total_days_in_month} = {percentage}%")
                    else:
                        values.append(0)
                        days_info.append("0/0")
                        print(f"  └─ Boolean: No hay días registrados en {month_name}")
                else:
                    # Para campos numéricos (excepto mood)
                    if field_name == 'mood':
                        # Para mood, no calculamos promedio, mantenemos los valores únicos
                        unique_moods = list(set([str(v) for v in month_values if v]))
                        values.append(unique_moods)
                        days_info.append("")
                        print(f"  └─ Mood: valores únicos = {unique_moods}")
                    else:
                        numeric_values = [v for v in month_values if isinstance(v, (int, float)) and v is not None]
                        if numeric_values:
                            avg_value = sum(numeric_values) / len(numeric_values)
                            values.append(round(avg_value, 1))
                            days_info.append("")
                            print(f"  └─ Numérico: promedio = {avg_value}")
                        else:
                            values.append(0)
                            days_info.append("")
                            print(f"  └─ No hay valores numéricos válidos")
            else:
                if field_name == 'mood':
                    values.append([])
                else:
                    values.append(0)
                days_info.append("")
                print(f"🔍 DEBUG: {month_name} sin datos")
        
        print(f"🔍 DEBUG get_yearly_data FINAL: Labels: {labels}")
        print(f"🔍 DEBUG get_yearly_data FINAL: Values: {values}")
        
        result = {
            'labels': labels,
            'values': values,
            'days_info': days_info,
            'period': 'yearly',
            'year': target_year
        }
        
        print(f"🔍 DEBUG get_yearly_data: ===== RESULTADO FINAL =====")
        print(f"  Labels count: {len(result['labels'])}")
        print(f"  Values count: {len(result['values'])}")
        print(f"  ======================================")
        
        return result
    
    @classmethod
    def get_specific_month_data(cls, user, field_name, year, month):
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

        print(f"DEBUG: get_specific_month_data {field_name} en {month}/{year}, entradas encontradas: {entries.count()}")

        data = {}
        current_date = start_date
        while current_date <= end_date:
            data[current_date] = None
            current_date += timedelta(days=1)

        for entry in entries:
            if hasattr(entry, field_name):
                data[entry.date] = getattr(entry, field_name)
            elif field_name.startswith('habit_'):
                habit_value = entry.custom_habits_data.get(field_name)
                data[entry.date] = habit_value


        return {
            'labels': [date.strftime('%d/%m') for date in data.keys()],
            'values': list(data.values()),
            'period': 'specific_month',
        }
    


    @classmethod 
    def get_all_stats_for_user(cls, user, period='weekly', year=None, month=None):
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
            elif period == 'yearly':
                data = cls.get_yearly_data(user, field)
            elif period == 'specific_month':
                data = cls.get_specific_month_data(user, field, year, month)
            else: 
                data = cls.get_weekly_data(user, field)  # Por defecto semanal
            
            stats.append({
                'id': f'journal_{field}',
                'field': field,
                'field_display': config['name'],
                'field_name': field,
                'field_type': 'boolean' if field == 'exercise' else 'numeric',
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
            habit_field_name = f'habit_{habit.id}'
            color = habit_colors[index % len(habit_colors)]

            # Obtener datos desde custom_habits_data del Journal (no desde HabitTracking)
            if period == 'weekly':
                data = cls.get_weekly_data(user, habit_field_name)
            elif period == 'monthly':
                data = cls.get_monthly_data(user, habit_field_name)
            elif period == 'yearly':
                data = cls.get_yearly_data(user, habit_field_name)
            elif period == 'specific_month':
                data = cls.get_specific_month_data(user, habit_field_name, year, month)
            else:
                data = cls.get_weekly_data(user, habit_field_name)
            
            stats.append({
                'id': f'habit_{habit.id}',
                'field': habit_field_name,
                'field_display': habit.name,
                'field_name': habit_field_name,
                'field_type': habit.type,
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
    
    def get_yearly_tracking(self, year=None):
        """Obtiene datos de seguimiento anual para este hábito desde HabitTracking"""
        import calendar
        from collections import defaultdict
        from datetime import datetime

        if year is None:
            # Usar el año más reciente con datos para este hábito
            tracking_entries = self.tracking_entries.all().order_by('date')
            if tracking_entries.exists():
                years_with_data = tracking_entries.dates('date', 'year')
                current_year = datetime.now().year
                
                if tracking_entries.filter(date__year=current_year).exists():
                    year = current_year
                else:
                    year = years_with_data.last().year
            else:
                year = datetime.now().year

        tracking = self.tracking_entries.filter(date__year=year).order_by('date')
        monthly_data = defaultdict(list)
        monthly_dates = defaultdict(set)

        for entry in tracking:
            month_name = calendar.month_name[entry.date.month]
            month_num = entry.date.month

            monthly_dates[month_name].add(entry.date)
            
            if self.type == 'boolean':
                value = entry.boolean_value
            elif self.type == 'integer':
                value = entry.integer_value
            elif self.type == 'float':
                value = entry.float_value
            else:
                value = None   

            if value is not None:
                monthly_data[month_name].append(value)
        
        labels = []
        values = []
        days_info = []

        for month_num in range(1, 13):
            month_name = calendar.month_name[month_num]
            labels.append(month_name[:3])
            
            if month_name in monthly_data and monthly_data[month_name]:
                month_values = monthly_data[month_name]

                if self.type == 'boolean':
                    if month_name in monthly_dates:
                        first_date = min(monthly_dates[month_name])
                        year_for_month = first_date.year
                        total_days_in_month = calendar.monthrange(year_for_month, month_num)[1]

                        days_completed = sum(1 for v in month_values if v is True)

                        percentage = round((days_completed / total_days_in_month) * 100, 1)
                    
                        values.append(percentage)
                        days_info.append(f"{days_completed}/{total_days_in_month}")
                    else:
                        values.append(0)
                        days_info.append("0/0")

                else:
                    # Para hábitos numéricos: calcular promedio
                    numeric_values = [float(v) for v in month_values if v is not None]
                    if numeric_values:
                        avg_value = sum(numeric_values) / len(numeric_values)
                        values.append(round(avg_value, 1))
                        days_info.append("")
                    else:
                        values.append(0)
                        days_info.append("")
            else:
                values.append(0)
                days_info.append("")

        return {
            'labels': labels,
            'values': values,
            'days_info': days_info,
            'period': 'yearly',
            'year': year
        }
    
    def get_specific_month_tracking(self, year, month):
        """Obtiene datos de seguimiento de mes específico para este hábito desde HabitTracking"""
        from calendar import monthrange

        if year is None or month is None:
            now = timezone.now()
            year = now.year
            month = now.month

        _, last_day = monthrange(year, month)
        start_date = timezone.datetime(year, month, 1).date()
        end_date = timezone.datetime(year, month, last_day).date()

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
            'values': list(data.values()),
            'period': 'specific_month'
        }    

        

        
        



