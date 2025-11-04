from datetime import timedelta, datetime
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
try:
    from haystack.query import SearchQuerySet
    from haystack.inputs import AutoQuery
    HAYSTACK_AVAILABLE = True
except Exception:
    HAYSTACK_AVAILABLE = False


@login_required
def home(request):
    return render(request, 'home.html')

@login_required 
def journal_list(request):
    journals = Journal.objects.filter(user=request.user).order_by('-date')

    date_filter = request.GET.get('date')
    mood_filter = request.GET.get('mood')
    exercise_filter = request.GET.get('excercise')
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


# @login_required
# def journal_edit(request, pk):
#     journal = get_object_or_404(Journal, pk=pk, user=request.user)
#     user_habits = CustomHabit.objects.filter(user=request.user, is_active=True)

#     habit_values = journal.custom_habits_data or {}
#     for habit in user_habits:
#         key = f"habit_{habit.id}"
#         habit.current_value = habit_values.get(key, "")

#     if request.method == 'POST':
#         form = JournalForm(request.POST, request.FILES, instance=journal, user=request.user)
#         if form.is_valid():
#             new_date = form.cleaned_data.get('date')
#             conflict = Journal.objects.filter(user=request.user, date=new_date).exclude(pk=journal.pk).first()
#             if conflict:
#                 messages.error(request, "Ya existe otro diario en la fecha seleccionada.")
#             else:
#                 habit_data = {}
#                 for habit in user_habits:
#                     field = f"habit_{habit.id}"
#                     if habit.type == "boolean":
#                         habit_data[field] = field in request.POST
#                     else:
#                         val = request.POST.get(field, "")
#                         habit_data[field] = int(val) if val.isdigit() else val

#                 journal.custom_habits_data = habit_data
#                 form.save()
#                 messages.success(request, "Diario actualizado.")
#                 return redirect('journal_list')
#     else:
#         form = JournalForm(instance=journal, user=request.user)

#     return render(request, 'bullet_journal/journal/edit_journal.html', {
#         'form': form,
#         'journal': journal,
#         'custom_habits': user_habits,
#     })

@login_required
def journal_edit(request, pk):
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    user_habits = CustomHabit.objects.filter(user=request.user, is_active=True)

    if request.method == 'POST':
        print(f"🔍 DEBUG: POST data recibido: {dict(request.POST)}")  # NUEVO DEBUG
        # Parse date safely
        date_str = request.POST.get('date') or ''
        try:
            new_date = datetime.fromisoformat(date_str).date() if date_str else journal.date
        except Exception:
            new_date = journal.date

        # check conflict (another journal same user + date)
        conflict = Journal.objects.filter(user=request.user, date=new_date).exclude(pk=journal.pk).first()
        if conflict:
            messages.error(request, "Ya existe otro diario en la fecha seleccionada.")

            for habit in user_habits:
                field_name = f'habit_{habit.id}'
                if journal.custom_habits_data and field_name in journal.custom_habits_data:
                    habit.current_value = journal.custom_habits_data[field_name]
                else:
                    habit.current_value = None

            sleep_hours_options = [4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 12]
            water_glasses_options = list(range(1, 13))  # [1, 2, 3, ..., 12]

            # re-render with existing data
            return render(request, 'bullet_journal/journal/edit_journal.html', {
                'journal': journal,
                'custom_habits': user_habits,
                'sleep_hours_options': sleep_hours_options,  # ← AGREGAR
                'water_glasses_options': water_glasses_options,  # ← AGREGAR
            })
        


        # assign simple fields
        journal.date = new_date
        journal.mood = request.POST.get('mood', journal.mood)
        # numeric fields: try to parse, keep existing if invalid
        try:
            journal.sleep_hours = float(request.POST.get('sleep_hours')) if request.POST.get('sleep_hours') not in (None, '') else journal.sleep_hours
        except Exception:
            pass
        try:
            journal.water_glasses = int(request.POST.get('water_glasses')) if request.POST.get('water_glasses') not in (None, '') else journal.water_glasses
        except Exception:
            pass
        # checkbox
        journal.exercise = True if request.POST.get('exercise') in ('on', 'true', '1') else False

        # build custom_habits_data from POST using habit ids
        habit_data = journal.custom_habits_data or {}
        print(f"🔍 DEBUG: Habit data inicial: {habit_data}")  # NUEVO DEBUG

        for habit in user_habits:
            key = f"habit_{habit.id}"
            print(f"🔍 DEBUG: Procesando hábito {habit.name} ({key})")  # NUEVO DEBUG
            
            if habit.type == 'boolean':
                value = key in request.POST
                habit_data[key] = value
                print(f"  └─ Boolean: {value}")  # NUEVO DEBUG
            else:
                val = request.POST.get(key)
                print(f"  └─ Valor raw: '{val}'")  # NUEVO DEBUG
                
                if val is None or val == '':
                    habit_data[key] = None
                    print(f"  └─ Guardado como: None")  # NUEVO DEBUG
                else:
                        # try convert integer if expected
                    if habit.type == 'integer':
                        try:
                            converted_val = int(val)
                            habit_data[key] = converted_val
                            print(f"  └─ Convertido a int: {converted_val}")  # NUEVO DEBUG
                        except Exception as e:
                            habit_data[key] = val
                            print(f"  └─ Error convirtiendo, guardado como string: {val}")  # NUEVO DEBUG
                    else:
                        habit_data[key] = val
                        print(f"  └─ Guardado como string: {val}")  # NUEVO DEBUG

        journal.custom_habits_data = habit_data
        print(f"🔍 DEBUG: Habit data final: {habit_data}")  # NUEVO DEBUG

        # save journal
        journal.save()
        print(f"✅ DEBUG: Journal guardado con hábitos: {journal.custom_habits_data}")  # NUEVO DEBUG

        messages.success(request, "Diario actualizado correctamente.")
        return redirect('journal_list')
    
    print(f"🔍 DEBUG: GET - Journal custom_habits_data: {journal.custom_habits_data}")  # NUEVO DEBUG

    for habit in user_habits:
        field_name = f'habit_{habit.id}'
        if journal.custom_habits_data and field_name in journal.custom_habits_data:
            habit.current_value = journal.custom_habits_data[field_name]
            print(f"🔍 DEBUG: {habit.name} valor actual: {habit.current_value}")  # NUEVO DEBUG
        else:
            habit.current_value = None
            print(f"🔍 DEBUG: {habit.name} sin valor previo")  # NUEVO DEBUG
            
    sleep_hours_options = [4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 12]
    water_glasses_options = list(range(1, 13))  # [1, 2, 3, ..., 12]
    # GET: render form with journal + habits
    return render(request, 'bullet_journal/journal/edit_journal.html', {
        'journal': journal,
        'custom_habits': user_habits,
        'sleep_hours_options': sleep_hours_options,  # ← AGREGAR
        'water_glasses_options': water_glasses_options,  # ← AGREGAR
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

    specific_year = request.GET.get('year')
    specific_month = request.GET.get('month')

    if period not in ['weekly', 'monthly', 'yearly', 'specific_month']:
        period = 'weekly'
    
    journals = Journal.objects.filter(user=user)
    print(f"DEBUG: Journals encontrados: {journals.count()}")
    for j in journals:
        print(f"DEBUG: - {j.date}: water={j.water_glasses}, sleep={j.sleep_hours}, exercise={j.exercise}")
        if j.custom_habits_data:
            print(f"  Hábitos: {j.custom_habits_data}")
    
    try:
        if period == 'specific_month' and specific_year and specific_month:
            all_stats = Journal.get_all_stats_for_user(
                user, 
                period=period,
                year=int(specific_year),
                month=int(specific_month)
            )
        else:
            all_stats = Journal.get_all_stats_for_user(user, period=period)
        print(f"DEBUG: Stats generadas: {len(all_stats)} estadísticas")
        
        for stat in all_stats:
            print(f"DEBUG: {stat['field_display']} - Valores: {stat['data']['values']}")
            
    except Exception as e:
        print(f"DEBUG: Error generando stats: {e}")
        import traceback
        traceback.print_exc()
        all_stats = []

    import calendar 
    from datetime import datetime

    current_year = datetime.now().year
    months_data = []

    years_with_data = journals.dates('date', 'year', order='DESC')
    available_years = [d.year for d in years_with_data] if years_with_data else [current_year]
   
    print(f"DEBUG: Años con datos: {available_years}")

    if years_with_data:
        for year_obj in years_with_data:
            year = year_obj.year
            print(f"DEBUG: Procesando año {year}")
            
            # Obtener meses con datos para este año
            months_in_year = journals.filter(date__year=year).dates('date', 'month', order='DESC')
            print(f"DEBUG: Meses en {year}: {[m.month for m in months_in_year]}")

            for month_obj in months_in_year:
                month = month_obj.month
                count = journals.filter(date__year=year, date__month=month).count()
                
                months_data.append({
                    'year': year,
                    'month': month,
                    'month_name': calendar.month_name[month],
                    'display': f"{calendar.month_name[month]} {year}",
                    'count': count
                })
                print(f"DEBUG: Agregado mes: {calendar.month_name[month]} {year} ({count} entradas)")
    
    print(f"DEBUG: Months_data generado: {months_data}")
    
    stats_json = json.dumps(all_stats, default=str)
    print(f"DEBUG: JSON final: {stats_json}")

    period_info = {
        'period': period,
        'year': specific_year,
        'month': specific_month,
        'month_name': calendar.month_name[int(specific_month)] if specific_month else None
    }

    return render(request, 'bullet_journal/journal/stadistics.html', {
        'stats': all_stats,
        'stats_json': stats_json,
        'journals_count': journals.count(),
        'current_period': period,
        'available_years': available_years,
        'months_data': months_data,
        'current_year': current_year,
        'period_info': period_info,

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

    active_count = habits.filter(is_active=True).count()
    inactive_count = habits.count() - active_count
    return render(request, 'bullet_journal/journal/manage_habits.html', {
        'form': form,
        'habits': habits,
        'active_count': active_count,
        'inactive_count': inactive_count,
    })

# En bullet_journal/views/habit_views.py - AGREGAR nueva vista

@login_required
def edit_habit(request, habit_id):
    """Vista para editar un hábito personalizado"""
    habit = get_object_or_404(CustomHabit, id=habit_id, user=request.user)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        goal_value = request.POST.get('goal_value')
        unit = request.POST.get('unit', '').strip()
        
        # Validaciones
        if not name:
            messages.error(request, 'El nombre del hábito es obligatorio.')
            return render(request, 'bullet_journal/journal/edit_habit.html', {'habit': habit})
        
        # Verificar que no exista otro hábito con el mismo nombre (excepto el actual)
        if CustomHabit.objects.filter(user=request.user, name=name).exclude(id=habit.id).exists():
            messages.error(request, 'Ya tienes un hábito con ese nombre.')
            return render(request, 'bullet_journal/journal/edit_habit.html', {'habit': habit})
        
        # Validar goal_value
        if goal_value:
            try:
                goal_value = int(goal_value)
                if goal_value <= 0:
                    messages.error(request, 'El valor de la meta debe ser mayor a 0.')
                    return render(request, 'bullet_journal/journal/edit_habit.html', {'habit': habit})
            except ValueError:
                messages.error(request, 'El valor de la meta debe ser un número válido.')
                return render(request, 'bullet_journal/journal/edit_habit.html', {'habit': habit})
        else:
            goal_value = None
        
        # Actualizar el hábito
        habit.name = name
        habit.description = description if description else None
        
        habit.goal_value = goal_value
        habit.unit = unit if unit else None
        habit.save()
        
        messages.success(request, f'Hábito "{habit.name}" actualizado correctamente.')
        return redirect('manage_habits')
    
    return render(request, 'bullet_journal/journal/edit_habit.html', {'habit': habit})

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
            return redirect('manage_habits')  
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

#@login_required
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
        # Intento Haystack (full-text). Si falla o no hay resultados para el usuario, usamos ORM como fallback.
        if HAYSTACK_AVAILABLE:
            try:
                sqs = SearchQuerySet().models(Journal).filter(content=AutoQuery(query)).load_all()
                diary_entries = []
                for r in sqs:
                    obj = getattr(r, 'object', None)
                    if obj and hasattr(obj, 'user') and obj.user_id == getattr(request.user, 'id', None):
                        diary_entries.append(obj)
                # si no hay resultados validados por usuario, fallback ORM
                if not diary_entries:
                    raise Exception("Haystack no devolvió resultados para el usuario, fallback ORM")
            except Exception:
                diary_entries = Journal.objects.filter(user=request.user).filter(
                    Q(title__icontains=query) | Q(diary_entry__icontains=query)
                ).order_by('-date')
        else:
            diary_entries = Journal.objects.filter(user=request.user).filter(
                Q(title__icontains=query) | Q(diary_entry__icontains=query)
            ).order_by('-date')
    else:
        diary_entries = Journal.objects.filter(user=request.user).order_by('-date')

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
