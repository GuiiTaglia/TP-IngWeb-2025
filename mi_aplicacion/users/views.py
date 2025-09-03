from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from bullet_journal.views.journal_views import home

def inicio(request):
    return render(request, 'inicio.html')

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registro.html', {'form': form})

@login_required
def logout(request):
    return redirect('inicio.html')

@login_required
def redirigir_post_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')
        else:
            return redirect('/home/')
