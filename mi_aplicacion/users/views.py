from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm



@login_required
def pagina_secundaria(request):
    return render(request, 'pagina_secundaria.html')

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('pagina_secundaria')
    else:
        form = UserCreationForm()
    return render(request, 'registro.html', {'form': form})
