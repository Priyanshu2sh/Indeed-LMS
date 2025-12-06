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

handler404 = views.PAGE_NOT_FOUND

urlpatterns = [
    path('admin/', admin.site.urls),

    # dashboard url
    path('dashboard/', include('dashboard.urls'), name='dashboard'),

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
    path('accounts/verify', user_login.VERIFY_OTP, name='verify_otp'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profiles', user_login.PROFILE, name='profile'),
    path('accounts/profiles/update', user_login.PROFILE_UPDATE, name='profile_update'),
    path('checkout/<slug:slug>', views.CHECKOUT, name='checkout'),
    path('my-course', views.MY_COURSE, name='my_course'),
    path('verify_payment', views.VERIFY_PAYMENT, name='verify_payment'),
    path('course/watch-course/<slug:slug>', views.WATCH_COURSE, name='watch_course'),
    path("save-video-progress/", views.save_video_progress, name="save_video_progress"),
    path('blog-detail/<int:pk>', views.blog_detail, name='blog_detail'),
    path('api/check_user_in_lms/', user_login.check_user_exists),
    path('api/update_user_in_lms/', user_login.update_user),
    
    
    path('blog/<int:post_id>/', views.add_blog_comment, name='add_blog_comment'),
    path('my-certificates/', views.my_certificates, name='my_certificates'),
    path('certificates/<int:pk>', views.view_certificate, name='view_certificate'),
    path('start_assessment/<int:pk>', views.start_assessment, name='start_assessment'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:course_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:course_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('certification/<str:randrand>', views.display_certificate, name='display_certificate'),
    path('wishlist/ajax-toggle/', views.toggle_wishlist_ajax, name='toggle_wishlist_ajax'),

    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('cancellation-refund/', views.cancellation_refund, name='cancellation_refund'),
    path('shipping-exchange/', views.shipping_exchange, name='shipping_exchange'),
    path('course-enquiry/<slug:slug>', views.course_enquiry, name='course_enquiry'),


    # Interview Practice Pages
    path('interview-practice/', views.interview_practice, name='interview_practice'),
    path('interview/', views.interview_page, name='interview_page'),
    
    # Demo-related URLs
    path('save-demo-inputs/', views.save_demo_inputs, name='save_demo_inputs'),
    path('create-demo-order/', views.create_demo_order, name='create_demo_order'),
    path('verify-demo-payment/', views.verify_demo_payment, name='verify_demo_payment'),
    path('start-demo/', views.start_demo, name='start_demo'),
    path('demo-payment/', views.demo_payment, name='demo_payment'),
    path('demo-config-api/', views.demo_config_api, name='demo_config_api'),
    
    # Subscription-related URLs (NEW)
    path('save-subscription-inputs/', views.save_subscription_inputs, name='save_subscription_inputs'),
    path('create-subscription-order/', views.create_subscription_order, name='create_subscription_order'),
    path('verify-subscription-payment/', views.verify_subscription_payment, name='verify_subscription_payment'),
    path('subscription-status/', views.subscription_status, name='subscription_status'),
    
    # Admin helper (optional, for manual grants)
    # path('admin/grant-subscription/<int:user_id>/', views.admin_grant_subscription, name='admin_grant_subscription'),
    
    # Order failed page
    path('order-failed/', views.order_failed, name='order_failed'),
    path('order-failed/<str:order_id>/', views.order_failed, name='order_failed'),



] + static(settings.MEDIA_URL,document_root = settings.MEDIA_ROOT)
