from django import forms
from .models import Journal, StatsPreference

class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ['date', 'mood', 'sleep_hours', 'water_glasses', 'exercise', 'image']

#Esto permite que se pueda crear un journal desde un view usando un ModelForm

class StatsPreferenceForm(forms.ModelForm):
    class Meta:
        model = StatsPreference
        fields = ['field', 'period', 'chart_type', 'is_visible', 'display_order']
        widgets = {
            'display_order': forms.NumberInput(attrs={'min': 0}),
        }