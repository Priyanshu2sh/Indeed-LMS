from django.shortcuts import redirect, render
from .models import User, Payment, UserCourse, UserProfile
from django.contrib import messages
from django.contrib.auth import login, logout
import random
from .send_otp import send_otp_to_email
from datetime import date
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests

def REGISTER(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        otp = random.randint(100000, 999999)

        user = User.objects.filter(email=email).first()
        if user:
            user_profile = UserProfile.objects.filter(user=user).first()
            if user_profile:
                user_profile.otp = otp
            else:
                user_profile = UserProfile(user=user, otp=otp)
        else:
            check_url = 'http://127.0.0.1:8001/accounts/api/check_user_in_indeed/'
            try:
                res = requests.post(check_url, data={'email': email}, timeout=5)
            except requests.exceptions.RequestException:
                print('message: Could not verify user in Indeed.')

            user = User(
                email=email,
            )
            user_profile = UserProfile(user=user, otp=otp)
            user.save()

        user_profile.save()
        send_otp_to_email(email, f"{user.first_name} {user.last_name}", otp)
        request.session['email'] = email
        return redirect('verify_otp')
    return render(request, 'registration/register.html')

def VERIFY_OTP(request):
    if request.method == 'POST':
        email = request.session.get('email')
        otp = request.POST.get('otp')

        try:
            user = User.objects.get(email=email)
            user_profile = UserProfile.objects.get(user=user)
        except User.DoesNotExist:
            messages.error(request,'No user found with this email. Please sign up.')
            return render(request, 'registration/register.html')

        if user_profile.otp == str(otp):
            user_profile.otp = ''
            user_profile.save()

            subscriptions_due = UserCourse.objects.filter(
                user=user,
                course__is_subscription=True,
                is_active=True,
                next_billing_date__lte=date.today()
            )

            for uc in subscriptions_due:
                payment_successful = Payment.objects.filter(user_course=uc, user=user, course=uc.course, status=True,date__date__gte=uc.next_billing_date).exists()
                if not payment_successful:
                    uc.is_active = False
                    uc.save()
                    
            login(request,user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid OTP')

    return render(request, 'registration/verify_otp.html')

def PROFILE(request):
    return render(request, 'registration/profile.html')

def PROFILE_UPDATE(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        user_id = request.user.id

        user = User.objects.get(id=user_id)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        check_url = 'http://127.0.0.1:8001/accounts/api/update_user_in_indeed/'
        try:
            res = requests.post(check_url, data={'email': email, "first_name": first_name, "last_name": last_name}, timeout=5)
        except requests.exceptions.RequestException:
            print('message: Could not verify user in Indeed.')
        messages.success(request,'Profile updated successfully. ')
        return redirect('profile')
    
@api_view(['POST'])
def check_user_exists(request):
    email = request.data.get('email')
    if User.objects.filter(email=email).exists():
        return Response({'created': False}, status=200)
    else: 
        user = User(email=email)
        user.save()
        return Response({'created': True}, status=200)

@api_view(['POST'])
def update_user(request):
    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    
    user = User.objects.filter(email=email).first()
    if not user:
        return Response({'error': "User not found"}, status=200)
    else:
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return Response({'message': "Profile updated successfully"}, status=200)