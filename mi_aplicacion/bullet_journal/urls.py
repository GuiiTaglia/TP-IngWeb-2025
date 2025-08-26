from django.urls import path
from .views.journal_views import journal_list, journal_detail, journal_create, journal_edit
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('journals/', journal_list, name='journal_list'),
    path('journals/<int:pk>/', journal_detail, name='journal_detail'),
    path('journals/create/', journal_create, name='journal_create'),
    path('journals/<int:pk>/edit/', journal_edit, name='journal_edit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
