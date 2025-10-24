from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.management import call_command
import traceback
import os

@require_http_methods(["GET"])
def rebuild_index(request):
 
    token_env = os.environ.get("REBUILD_INDEX_TOKEN")
  
    if token_env:
        token_req = request.GET.get("token")
        if token_req != token_env:
            return HttpResponse("Forbidden", status=403)

    try:
        call_command('update_index', verbosity=1, interactive=False)
        return HttpResponse("Índice rebuilded OK", status=200)
    except Exception as e:
        tb = traceback.format_exc()
        return HttpResponse(f"Error rebuilding index: {str(e)}\n\n{tb}", status=500)