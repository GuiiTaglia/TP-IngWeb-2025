from datetime import timedelta
from bullet_journal.models import Journal, CustomHabit, StatsPreference as models
from bullet_journal.forms import JournalForm, CustomHabitForm, StatsPreferenceForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import json
from django.utils.timezone import now
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.db.models import Q
from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet
from .models import Journal

@login_required
def home(request):
    return render(request, 'home.html')

@login_required 
def journal_list(request):
    journals = Journal.objects.filter(user=request.user).order_by('-date')

    date_filter = request.GET.get('date')
    mood_filter = request.GET.get('mood')
    exercise_filter = request.GET.get('exercise')
    horas_sueno = request.GET.get('sleep_hours')

    if date_filter:
        journals = journals.filter(date=date_filter)
    if mood_filter:
        journals = journals.filter(mood__icontains=mood_filter)
    if exercise_filter in ['true', 'false']:
        journals = journals.filter(exercise=(exercise_filter == 'true'))
    if horas_sueno:
        journals = journals.filter(sleep_hours=horas_sueno)

    moods_disponibles = Journal.objects.filter(user=request.user).values_list('mood', flat=True).distinct()

    existe_hoy = journals.filter(date=now().date()).exists()

    user_habits = CustomHabit.objects.filter(user=request.user)
    
    return render(request, 'bullet_journal/journal/list.html', {
        'journals': journals,
        'moods_disponibles': moods_disponibles,
        'existe_hoy': existe_hoy,
        'horas_sueno': horas_sueno,
        'sleep_hours_range': range(1, 13),  
        'user_habits': user_habits
    })


@login_required
def journal_detail(request, pk):
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    user_habits = CustomHabit.objects.filter(user=request.user)
    return render(request, 'bullet_journal/journal/detail.html', {
        'journal': journal,
        'user_habits': user_habits
        })


@login_required
def journal_create(request):
    print(f"DEBUG: Iniciando journal_create - Método: {request.method}")
    
    if request.method == 'POST':
        print(f"DEBUG: Usuario: {request.user}")
        form = JournalForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            date = form.cleaned_data['date']
            print(f"DEBUG: Fecha: {date}")
            
            existing_count = Journal.objects.filter(user=request.user, date=date).count()
            print(f"DEBUG: Journals existentes para {date}: {existing_count}")
            
            try:
                journal = Journal.objects.get(user=request.user, date=date)
                print(f"DEBUG: Journal existente encontrado ID: {journal.id}")
                
                journal.mood = form.cleaned_data['mood']
                journal.sleep_hours = form.cleaned_data.get('sleep_hours')
                journal.water_glasses = form.cleaned_data.get('water_glasses')
                journal.exercise = form.cleaned_data.get('exercise', False)
                
                if form.cleaned_data.get('image'):
                    journal.image = form.cleaned_data['image']
                
                custom_habits_data = {}
                for field_name, value in form.cleaned_data.items():
                    if field_name.startswith('habit_'):
                        custom_habits_data[field_name] = value
                
                journal.custom_habits_data = custom_habits_data
                journal.save()
                print(f"DEBUG: Journal actualizado exitosamente")
                action = "actualizado"
                
            except Journal.DoesNotExist:
                print(f"DEBUG: Creando nuevo journal")
                custom_habits_data = {}
                for field_name, value in form.cleaned_data.items():
                    if field_name.startswith('habit_'):
                        custom_habits_data[field_name] = value
                
                journal = Journal(
                    user=request.user,
                    date=date,
                    mood=form.cleaned_data['mood'],
                    sleep_hours=form.cleaned_data.get('sleep_hours'),
                    water_glasses=form.cleaned_data.get('water_glasses'),
                    exercise=form.cleaned_data.get('exercise', False),
                    custom_habits_data=custom_habits_data
                )
                
                if form.cleaned_data.get('image'):
                    journal.image = form.cleaned_data['image']
                
                journal.save()
                print(f"DEBUG: Nuevo journal creado ID: {journal.id}")
                action = "creado"
            
            except Exception as e:
                print(f"DEBUG: Error inesperado: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"Error al guardar: {e}")
                return render(request, 'bullet_journal/journal/new_journal.html', {
                    'form': form, 
                    'custom_habits': CustomHabit.objects.filter(user=request.user, is_active=True)
                })
            
            messages.success(request, f"Journal {action} correctamente 🎉")
            return redirect('journal_list')
        else:
            print(f"DEBUG: Errores del formulario: {form.errors}")
    else:
        form = JournalForm(user=request.user)
        today = timezone.now().date()
        existing_journal = Journal.objects.filter(user=request.user, date=today).first()
        if existing_journal:
            form = JournalForm(instance=existing_journal, user=request.user)
            load_custom_habits_data(form, request.user, today)

    custom_habits = CustomHabit.objects.filter(user=request.user, is_active=True)
  

    return render(request, 'bullet_journal/journal/new_journal.html', {
        'form': form, 
        'custom_habits': custom_habits
    })


@login_required
def journal_edit(request, pk):
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    
    if request.method == "POST":
        form = JournalForm(request.POST, request.FILES, instance=journal, user=request.user)
        
        if form.is_valid():
            custom_habits_data = {} 
            for field_name, value in form.cleaned_data.items():
                if field_name.startswith('habit_'):
                    custom_habits_data[field_name] = value
                
            journal = form.save()
            journal.custom_habits_data = custom_habits_data
            journal.save()

            messages.success(request, "Journal actualizado correctamente 🎉")
            return redirect('journal_list')
    else:
        form = JournalForm(instance=journal, user=request.user)
        load_custom_habits_data(form, request.user, journal.date)
    
    return render(request, 'bullet_journal/journal/edit_journal.html', {
        'form': form,
        'journal': journal,
        'custom_habits': CustomHabit.objects.filter(user=request.user, is_active=True)
        })


@login_required
def calendar(request):
    return render(request, 'bullet_journal/journal/calendar.html')

@login_required
def to_do_list(request):
    return render(request, 'bullet_journal/journal/to_do_list.html')

@login_required
def stadistics(request):
    """Vista para mostrar estadísticas del journal y hábitos personalizados"""
    user = request.user
    period = request.GET.get('period', 'weekly')  
    
    journals = Journal.objects.filter(user=user)
    print(f"DEBUG: Journals encontrados: {journals.count()}")
    for j in journals:
        print(f"DEBUG: - {j.date}: water={j.water_glasses}, sleep={j.sleep_hours}, exercise={j.exercise}")
        if j.custom_habits_data:
            print(f"  Hábitos: {j.custom_habits_data}")
    
    try:
        all_stats = Journal.get_all_stats_for_user(user, period=period)
        print(f"DEBUG: Stats generadas: {len(all_stats)} estadísticas")
        
        for stat in all_stats:
            print(f"DEBUG: {stat['field_display']} - Valores: {stat['data']['values']}")
            
    except Exception as e:
        print(f"DEBUG: Error generando stats: {e}")
        import traceback
        traceback.print_exc()
        all_stats = []
    
    stats_json = json.dumps(all_stats, default=str)
    print(f"DEBUG: JSON final: {stats_json}")

    return render(request, 'bullet_journal/journal/stadistics.html', {
        'stats': all_stats,
        'stats_json': stats_json,
        'journals_count': journals.count(),
        'current_period': period,
    })

@login_required
def manage_habits(request):
    """Vista simple para gestionar hábitos personalizados"""
    if request.method == 'POST':
        form = CustomHabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            messages.success(request, f'Hábito "{habit.name}" creado exitosamente!')
            return redirect('manage_habits')
    else:
        form = CustomHabitForm()
    
    habits = CustomHabit.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'bullet_journal/journal/manage_habits.html', {
        'form': form,
        'habits': habits
    })

@login_required
def add_habit_quick(request):
    """Vista rápida para agregar un hábito desde el formulario del journal"""
    if request.method == 'POST':
        form = CustomHabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            messages.success(request, f'¡Hábito "{habit.name}" agregado! Ya aparece en tu formulario diario.')
            return redirect('journal_create')  # Volver al formulario del journal
        else:
            messages.error(request, 'Error creando el hábito. Revisa los datos.')
    else:
        form = CustomHabitForm()
    
    return render(request, 'bullet_journal/journal/add_habit_quick.html', {
        'form': form
    })

@login_required
def toggle_habit_status(request, habit_id):
    """Vista para activar/desactivar un hábito"""
    habit = get_object_or_404(CustomHabit, id=habit_id, user=request.user)
    habit.is_active = not habit.is_active
    habit.save()
    
    status = "activado" if habit.is_active else "desactivado"
    messages.success(request, f'Hábito "{habit.name}" {status}.')
    
    return redirect('manage_habits')

def load_custom_habits_data(form, user, date):
    """Función auxiliar para cargar datos existentes de hábitos en el formulario"""
    try:
        journal = Journal.objects.get(user=user, date=date)
        if journal.custom_habits_data:
            for field_name, value in journal.custom_habits_data.items():
                if field_name in form.fields and value is not None:
                    form.fields[field_name].initial = value
    except Journal.DoesNotExist:
        pass


# Agregar después de las vistas existentes:
@login_required
def diary_entry(request):
    """Vista para crear/editar entrada de diario personal"""
    today = timezone.now().date()
    
    # Verificar si ya existe una entrada para hoy
    journal, created = Journal.objects.get_or_create(
        user=request.user,
        date=today,
        defaults={
            'mood': '',
            'sleep_hours': None,
            'water_glasses': None,
            'exercise': False,
        }
    )
    
    if request.method == 'POST':
        # Actualizar campos del diario
        journal.title = request.POST.get('title', '')
        journal.diary_entry = request.POST.get('diary_entry', '')
        
        # Manejar imagen del diario
        if 'diary_image' in request.FILES:
            journal.diary_image = request.FILES['diary_image']
        
        journal.save()
        messages.success(request, '¡Tu entrada de diario ha sido guardada!')
        return redirect('diary_list')
    
    return render(request, 'bullet_journal/journal/diary_entry.html', {
        'journal': journal,
        'today': today,
    })

@login_required
# def diary_list(request):
#     """Vista para listar todas las entradas de diario"""
#     # Solo mostrar entradas que tengan título o texto de diario
#     query = request.GET.get('q', '').strip()  # texto de búsqueda

#     diary_entries = Journal.objects.filter(user=request.user)
    
#     diary_entry = diary_entries.exclude(
#         title__isnull=True, diary_entry__isnull=True
#     ).exclude(title='', diary_entry='')

#     if query:
#         diary_entries = diary_entries.filter(
#             Q(title__icontains=query) | Q(diary_entry__icontains=query)
#         )

#     diary_entries = diary_entries.order_by('-date')
    
#     return render(request, 'bullet_journal/journal/diary_list.html', {
#         'diary_entries': diary_entries,
#         'query': query,
#     })
@login_required
def diary_list(request):
    query = request.GET.get('q', '').strip()

    if query:
        results = SearchQuerySet().filter(content=AutoQuery(query))
        diary_entries = [r.object for r in results if r.object.user ==  request.user]
    else:
        diary_entries = Journal.objects.filter(user=request.user)

    return render(request, 'bullet_journal/journal/diary_list.html', {
        'diary_entries': diary_entries,
        'query': query,
        })
   


@login_required
def diary_detail(request, pk):
    """Vista para ver detalle de una entrada de diario"""
    diary_entry = get_object_or_404(Journal, pk=pk, user=request.user)
    
    return render(request, 'bullet_journal/journal/diary_detail.html', {
        'diary_entry': diary_entry,
    })
