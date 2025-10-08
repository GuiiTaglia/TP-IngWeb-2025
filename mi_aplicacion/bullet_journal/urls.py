from re import search
from django.urls import path
from .views.journal_views import calendar, home, journal_list, journal_detail, journal_create, journal_edit, stadistics, to_do_list, manage_habits, toggle_habit_status, add_habit_quick, diary_entry, diary_list, diary_detail
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import search_views

urlpatterns = [
    path('home/', home, name='home'),
    path('journals/', journal_list, name='journal_list'),
    path('journals/<int:pk>/', journal_detail, name='journal_detail'),
    path('journals/new_journal/', journal_create, name='journal_create'),
    path('journals/<int:pk>/edit/', journal_edit, name='journal_edit'),
    path('calendar/', calendar, name='calendar'),
    path('to_do_list/', to_do_list, name='to_do_list'),

    path('habits/manage/', manage_habits, name='manage_habits'),
    path('habits/add/', add_habit_quick, name='add_habit_quick'),
    path('habits/toggle/<int:habit_id>/', toggle_habit_status, name='toggle_habit_status'),

    path('diary/', diary_entry, name='diary_entry'),
    path('diary/list/', diary_list, name='diary_list'),
    path('diary/<int:pk>/', diary_detail, name='diary_detail'),
    path('stadistics/', stadistics, name='stadistics'),
    path('search/', search_views.search, name='search'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

