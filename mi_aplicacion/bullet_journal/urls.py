from django.urls import path
from . import views 
from .views.journal_views import journal_list, journal_detail, journal_create, journal_edit

urlpatterns = [
    path('journals/', views.journal_list, name='journal_list'),
    path('journals/create/', views.journal_create, name='journal_create'),
    path('journals/<int:pk>/', views.journal_detail, name='journal_detail'),
    path('journals/<int:pk>/edit/', views.journal_edit, name='journal_edit'),
]
