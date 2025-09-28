from bullet_journal.models import Journal, CustomHabit, HabitTracking, StatsPreference
from bullet_journal.forms import JournalForm, CustomHabitForm, StatsPreferenceForm, HabitTrackingForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import json


@login_required
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
# @login_required
# def journal_create(request):
#     if request.method == 'POST':
#         form = JournalForm(request.POST, request.FILES, user=request.user)
#         if form.is_valid():
#             date = form.cleaned_data['date']
            
#             #extrar habitos personalizados del formulario
#             custom_habits_data = {}
#             for field_name, value in form.cleaned_data.items():
#                 if field_name.startswith('habit_'):
#                     custom_habits_data[field_name] = value
            
#             #Usar update_or_create para evitar duplicados por fecha y usuario
#             journal, created = Journal.objects.update_or_create(
#                 user=request.user,
#                 date=date,
#                 defaults={
#                     'mood': form.cleaned_data['mood'],
#                     'sleep_hours': form.cleaned_data.get('sleep_hours'),
#                     'water_glasses': form.cleaned_data.get('water_glasses'),
#                     'exercise': form.cleaned_data.get('exercise', False),
#                     'image': form.cleaned_data.get('image'),
#                     'custom_habits_data': custom_habits_data
#                 }
#             )
#             action = "Creado" if created else "Actualizado"
#             messages.success(request, f"Journal {action} correctamente 🎉")
#             return redirect('journal_list')
#     else:
#         form = JournalForm(user=request.user)
#         #prellenar la fecha con la fecha actual
#         today = timezone.now().date()
#         existing_journal = Journal.objects.filter(user=request.user, date=today).first()
#         if existing_journal:
#             form = JournalForm(instance=existing_journal, user=request.user)
#             load_custom_habits_data(form, request.user, today)

#     return render(request, 'bullet_journal/journal/new_journal.html', {'form': form, 'custom_habits': CustomHabit.objects.filter(user=request.user, is_active=True) })
           

@login_required
def journal_create(request):
    print(f"DEBUG: Iniciando journal_create - Método: {request.method}")
    
    if request.method == 'POST':
        print(f"DEBUG: Usuario: {request.user}")
        form = JournalForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            date = form.cleaned_data['date']
            print(f"DEBUG: Fecha: {date}")
            
            # Verificar journals existentes
            existing_count = Journal.objects.filter(user=request.user, date=date).count()
            print(f"DEBUG: Journals existentes para {date}: {existing_count}")
            
            # Método más simple y directo
            try:
                # Intentar obtener journal existente
                journal = Journal.objects.get(user=request.user, date=date)
                print(f"DEBUG: Journal existente encontrado ID: {journal.id}")
                
                # Actualizar campos uno por uno
                journal.mood = form.cleaned_data['mood']
                journal.sleep_hours = form.cleaned_data.get('sleep_hours')
                journal.water_glasses = form.cleaned_data.get('water_glasses')
                journal.exercise = form.cleaned_data.get('exercise', False)
                
                if form.cleaned_data.get('image'):
                    journal.image = form.cleaned_data['image']
                
                # Extraer hábitos personalizados
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
                # Crear nuevo journal
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

    return render(request, 'bullet_journal/journal/new_journal.html', {
        'form': form, 
        'custom_habits': CustomHabit.objects.filter(user=request.user, is_active=True)
    })


@login_required
def journal_edit(request, pk):
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    
    if request.method == "POST":
        form = JournalForm(request.POST, request.FILES, instance=journal, user=request.user)
        
        if form.is_valid():
            #extraer habitos personalizados del formulario
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
    period = request.GET.get('period', 'weekly')  # Permitir cambiar período
    
    # DEBUG: Verificar journals del usuario
    journals = Journal.objects.filter(user=user)
    print(f"DEBUG: Journals encontrados: {journals.count()}")
    for j in journals:
        print(f"DEBUG: - {j.date}: water={j.water_glasses}, sleep={j.sleep_hours}, exercise={j.exercise}")
        if j.custom_habits_data:
            print(f"  Hábitos: {j.custom_habits_data}")
    
    # Obtener estadísticas
    try:
        all_stats = Journal.get_all_stats_for_user(user, period=period)
        print(f"DEBUG: Stats generadas: {len(all_stats)} estadísticas")
        
        # Verificar datos específicos
        for stat in all_stats:
            print(f"DEBUG: {stat['field_display']} - Valores: {stat['data']['values']}")
            
    except Exception as e:
        print(f"DEBUG: Error generando stats: {e}")
        import traceback
        traceback.print_exc()
        all_stats = []
    
    # Convertir los datos para Chart.js
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