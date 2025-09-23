from django.shortcuts import render

from app.models import *

# Create your views here.
def dashboard(request):
    return render(request, 'dashboard/dashboard.html')

def courses(request):
    courses = Course.objects.all()
    return render(request, 'dashboard/courses.html', {'courses': courses})

def authors(request):
    authors = Author.objects.all()
    return render(request, 'dashboard/authors.html', {'authors': authors})

def categories(request):
    categories = Categories.objects.all()
    return render(request, 'dashboard/categories.html', {'categories': categories})

def levels(request):
    levels = Level.objects.all()
    return render(request, 'dashboard/levels.html', {'levels': levels})