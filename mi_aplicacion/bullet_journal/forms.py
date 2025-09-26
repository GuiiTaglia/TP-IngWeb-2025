from django import forms
from .models import Journal, StatsPreference, CustomHabit, HabitTracking

class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ['date', 'mood', 'sleep_hours', 'water_glasses', 'exercise', 'image']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'mood': forms.TextInput(attrs={'placeholder': 'ej: feliz, cansado, motivado'}),
            'sleep_hours': forms.NumberInput(attrs={'step': '0.5', 'min': '0', 'max': '24'}),
            'water_glasses': forms.NumberInput(attrs={'min': '0'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar campos dinámicos para hábitos personalizados del usuario
        if user:
            custom_habits = CustomHabit.objects.filter(user=user, is_active=True)
            
            for habit in custom_habits:
                field_name = f'habit_{habit.id}'
                
                if habit.type == 'boolean':
                    self.fields[field_name] = forms.BooleanField(
                        required=False,
                        label=habit.name,
                        help_text=habit.description
                    )
                elif habit.type == 'integer':
                    self.fields[field_name] = forms.IntegerField(
                        required=False,
                        label=f"{habit.name} (cantidad)",
                        min_value=0,
                        help_text=habit.description
                    )
                elif habit.type == 'float':
                    self.fields[field_name] = forms.FloatField(
                        required=False,
                        label=f"{habit.name} (cantidad)",
                        min_value=0,
                        help_text=habit.description
                    )

#Esto permite que se pueda crear un journal desde un view usando un ModelForm

class StatsPreferenceForm(forms.ModelForm):
    class Meta:
        model = StatsPreference
        fields = ['field', 'period', 'chart_type', 'is_visible', 'display_order']
        widgets = {
            'display_order': forms.NumberInput(attrs={'min': 0}),
        }


class CustomHabitForm(forms.ModelForm):
    class Meta:
        model = CustomHabit
        fields = ['name', 'description', 'type']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'ej: Meditar, Leer páginas, Correr km'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción opcional del hábito'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
        }

class HabitTrackingForm(forms.ModelForm):
    class Meta:
        model = HabitTracking
        fields = ['boolean_value', 'integer_value', 'float_value', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Notas opcionales'}),
        }

    def __init__(self, *args, habit_type=None, **kwargs):
        super().__init__(*args, **kwargs)

        #ocultar campos no relevantes segun el tipo de habito
        if habit_type == 'boolean':
            self.fields.pop('integer_value', None)
            self.fields.pop('float_value', None)
            self.fields['boolean_value'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
            self.fields['boolean_value'].label = "¿Completado?"
            self.fields['boolean_value'].required = False
        
        elif habit_type == 'integer':
            self.fields.pop('boolean_value', None)
            self.fields.pop('float_value', None)
            self.fields['integer_value'].widget = forms.NumberInput(attrs={'min': '0', 'class': 'form-control'})
            self.fields['integer_value'].label = "Cantidad"
            self.fields['integer_value'].required = False
            
        elif habit_type == 'float':
            self.fields.pop('boolean_value', None)
            self.fields.pop('integer_value', None)
            self.fields['float_value'].widget = forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'class': 'form-control'})
            self.fields['float_value'].label = "Cantidad"
            self.fields['float_value'].required = False        

