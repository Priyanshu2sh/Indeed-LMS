from django.urls import path
from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('courses/', views.courses, name='courses'),
    path('authors/', views.authors, name='authors'),
    path('categories/', views.categories, name='categories'),
    path('levels/', views.levels, name='levels'),
    path('courses/edit/', views.edit_course, name='edit_course'),
    path('courses/delete/', views.delete_course, name='delete_course'),
    path('authors/edit/', views.edit_author, name='edit_author'),
    path('authors/delete/', views.delete_author, name='delete_author'),
    path('categories/edit/', views.edit_category, name='edit_category'),
    path('levels/edit/', views.edit_level, name='edit_level'),  # Add this line
    path('categories/add/', views.add_category, name='add_category'),  # Add this line
    path('categories/delete/', views.delete_category, name='delete_category'),  # Add this line
    path('videos/', views.videos, name='videos'),  # Add this line
    path('videos/edit/', views.edit_video, name='edit_video'),  # Add this line
    path('videos/delete/', views.delete_video, name='delete_video'),  
    path('videos/add/', views.add_video, name='add_video'),  # Add this line
    path('add_lesson/', views.add_lesson, name='add_lesson'),
    path('courses/add/', views.add_course, name='add_course'),  # <-- Add this line
    path('authors/add/', views.add_author, name='add_author'),
    path('login/', views.admin_login, name='adminlogin'),
    path('logout/', views.logout, name='logout'),
]