from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('courses/', views.courses, name='courses'),
    path('authors/', views.authors, name='authors'),
    path('categories/', views.categories, name='categories'),
    path('levels/', views.levels, name='levels'),
]