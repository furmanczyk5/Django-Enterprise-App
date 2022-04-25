from django.http import HttpResponse


def index(request):
    return HttpResponse("Viewing Celery Tasks")
