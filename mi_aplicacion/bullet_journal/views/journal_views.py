from bullet_journal.models import Journal
from bullet_journal.forms import JournalForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def home(request):
    return render(request, 'home.html')


@login_required 
def journal_list(request):
    journals = Journal.objects.filter(user=request.user).order_by('-date')

    # Filtros opcionales: por fecha, estado de ánimo, ejercicio
    date_filter = request.GET.get('date')
    mood_filter = request.GET.get('mood')
    exercise_filter = request.GET.get('exercise')

    if date_filter:
        journals = journals.filter(date=date_filter)
    if mood_filter:
        journals = journals.filter(mood__icontains=mood_filter)
    if exercise_filter in ['true', 'false']:
        journals = journals.filter(exercise=(exercise_filter == 'true'))

    # Obtener moods únicos de los journals de este usuario para el filtro dinámico
    moods_disponibles = Journal.objects.filter(user=request.user).values_list('mood', flat=True).distinct()

    return render(request, 'bullet_journal/journal/list.html', {
        'journals': journals,
        'moods_disponibles': moods_disponibles,
    })

# Detalle de un journal
@login_required
def journal_detail(request, pk):
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    return render(request, 'bullet_journal/journal/detail.html', {'journal': journal})

# Crear un journal
@login_required
def journal_create(request):
    if request.method == 'POST':
        form = JournalForm(request.POST, request.FILES)
        if form.is_valid():
            journal = form.save(commit=False)
            journal.user = request.user
            journal.save()
            messages.success(request, "Journal creado correctamente 🎉")
            return redirect('journal_list')
    else:
        form = JournalForm()
    return render(request, 'bullet_journal/journal/form.html', {'form': form})

@login_required
def journal_edit(request, pk):
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    
    if request.method == "POST":
        form = JournalForm(request.POST, request.FILES, instance=journal)
        if form.is_valid():
            form.save()
            return redirect('journal_detail', pk=journal.pk)
    else:
        form = JournalForm(instance=journal)
    
    return render(request, 'bullet_journal/journal/edit_journal.html', {'form': form, 'journal': journal})


