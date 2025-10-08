from django.urls import path
from . import views
from .views import CustomLoginView, CustomSignupView

app_name = 'users'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('signup/', CustomSignupView.as_view(), name='signup'),
    path('check-email/', views.check_email_view, name='check_email'),
    path('logout/', views.logout_view, name='logout'),
    path('redirigir/', views.redirigir_post_login, name='redirigir_post_login'),
]