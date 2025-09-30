from django import forms
from .models import Journal, StatsPreference, CustomHabit

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
        fields = ['name', 'description', 'type', 'goal_value', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'ej: Pasos diarios, Páginas leídas, Meditar',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Descripción opcional del hábito',
                'class': 'form-control'
            }),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'goal_value': forms.NumberInput(attrs={
                'placeholder': 'ej: 10000 (para pasos)',
                'class': 'form-control',
                'min': '1'
            }),
            'unit': forms.TextInput(attrs={
                'placeholder': 'ej: pasos, páginas, minutos',
                'class': 'form-control'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer goal_value y unit opcionales visualmente
        self.fields['goal_value'].required = False
        self.fields['unit'].required = False
        self.fields['description'].required = False


       

