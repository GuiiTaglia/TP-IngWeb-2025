from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
#from django.contrib.auth.forms import UserCreationForm
from bullet_journal.views.journal_views import home
from .forms import CustomUserCreationForm
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import logout as auth_logout

from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model, login


"""def inicio(request):
    return render(request, 'inicio.html')"""

User = get_user_model()
def inicio(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'inicio.html')



def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False 
            user.save()

            # preparar email
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            message = render_to_string('activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
            })

            send_mail(
                'Activa tu cuenta',
                message,
                None, 
                [user.email],
                fail_silently=False,
            )

            return render(request, 'check_email.html', {'email': user.email})
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, 'activation_success.html')
    else:
        return render(request, 'activation_invalid.html')

#def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})#

#def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

#def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

"""@login_required
def logout(request):
    return redirect('inicio.html')"""

def logout_view(request):
    auth_logout(request)
    return redirect('inicio')

    
@login_required
def redirigir_post_login(request):
    if request.user.is_superuser:
        return redirect('/admin/')
    else:
        return redirect('/home/')
