from django.urls import path
from . import views 
from .views.journal_views import journal_list, journal_detail, journal_create, journal_edit

path('journals/', journal_list, name='journal_list'),
path('journals/<int:id>/', journal_detail, name='journal_detail'),
path('journals/create/', journal_create, name='journal_create'),
path('journals/<int:id>/edit/', journal_edit, name='journal_edit'),
