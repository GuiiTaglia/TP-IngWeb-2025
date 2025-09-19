from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('register/', views.registro, name='registro'),
    path('login/', auth_views.LoginView.as_view(
    template_name='login.html',
    redirect_authenticated_user=True,
    next_page='redirigir_post_login'
), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('post_login/', views.redirigir_post_login, name='redirigir_post_login'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
]