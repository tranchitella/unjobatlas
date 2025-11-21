from django.http import HttpResponse


def index(request):
    """Home page view."""
    return HttpResponse("Welcome to UNJobAtlas - Django 4.2 LTS Application")
