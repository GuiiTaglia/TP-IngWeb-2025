from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from allauth.account.views import LoginView, SignupView

def inicio(request):
    """Vista de página de inicio"""
    if request.user.is_authenticated:
        return redirect('/home/')
    return render(request, 'inicio.html')

def logout_view(request):
    """Vista personalizada de logout"""
    auth_logout(request)
    return redirect('/')

@login_required
def redirigir_post_login(request):
    """Redireccionar después del login según tipo de usuario"""
    if request.user.is_superuser:
        return redirect('/admin/')
    else:
        return redirect('/home/')

# VISTAS PERSONALIZADAS PARA ALLAUTH
class CustomLoginView(LoginView):
    """Vista de login personalizada usando tu template"""
    template_name = 'login.html'

class CustomSignupView(SignupView):
    """Vista de registro personalizada usando tu template"""
    template_name = 'register.html'

def check_email_view(request):
    """Vista para mostrar mensaje de verificación de email"""
    email = request.session.get('account_verification_email', 'tu email')
    return render(request, 'check_email.html', {'email': email})