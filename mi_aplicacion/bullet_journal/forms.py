from django import forms
from .models import Journal

class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ['date', 'title', 'content', 'mood', 'sleep_hours', 'water_glasses', 'exercise', 'image']

#Esto permite que se pueda crear un journal desde un view usando un ModelForm
