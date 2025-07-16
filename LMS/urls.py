"""
URL configuration for LMS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from app import user_login
from app import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    path('base',views.BASE, name='base'),
    path('404',views.PAGE_NOT_FOUND,name='404'),
    path('',views.HOME, name='home'),
    path('courses',views.SINGLE_COURSE, name='single_course'),
    path('courses/filter-data',views.filter_data,name="filter-data"),
    path('courses/<slug:slug>',views.COURSE_DETAILS,name="course_details"),
    path('contact',views.CONTACT_US, name='contact_us'),
    path('about',views.ABOUT_US, name='about_us'),
    path('search',views.SEARCH_COURSE, name='search_course'),

    path('accounts/register', user_login.REGISTER, name='register'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dologin', user_login.DO_LOGIN, name='dologin'),
    path('accounts/profiles', user_login.PROFILE, name='profile'),
    path('accounts/profiles/update', user_login.PROFILE_UPDATE, name='profile_update'),
    path('checkout/<slug:slug>', views.CHECKOUT, name='checkout'),
    path('my-course', views.MY_COURSE, name='my_course'),
    path('verify_payment', views.VERIFY_PAYMENT, name='verify_payment'),
    path('course/watch-course/<slug:slug>', views.WATCH_COURSE, name='watch_course'),
    path("save-video-progress/", views.save_video_progress, name="save_video_progress"),
    path('blog-detail/', views.blog_detail, name='blog_detail'),

] + static(settings.MEDIA_URL,document_root = settings.MEDIA_ROOT)
