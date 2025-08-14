from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

def inicio(request):
    return render(request, 'inicio.html')

@login_required
def pagina_secundaria(request):
    return render(request, 'pagina_secundaria.html')

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('pagina_secundaria')
    else:
        form = UserCreationForm()
    return render(request, 'registro.html', {'form': form})
