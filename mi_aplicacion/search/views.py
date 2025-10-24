from django.core.management import call_command
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

@staff_member_required
def rebuild_index(request):
    try:
        call_command('update_index', verbosity=1)  # quitá interactive=False
        return HttpResponse("Index rebuilt successfully")
    except Exception as e:
        return HttpResponse(f"Error rebuilding index: {e}")