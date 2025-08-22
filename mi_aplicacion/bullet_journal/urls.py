from django.urls import path
from .views.journal_views import journal_list, journal_detail, journal_create

urlpatterns = [
    path('journals/', journal_list, name='journal_list'),
    path('journals/create/', journal_create, name='journal_create'),
    path('journals/<int:pk>/', journal_detail, name='journal_detail'),
]
