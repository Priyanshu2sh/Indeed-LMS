from collections import defaultdict
from time import time
from django.contrib import messages
from django.shortcuts import redirect, render
from app.models import *
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Count
import json

import razorpay
from LMS.settings import *

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def BASE(request):
    return render(request, 'base.html')


def HOME(request):
    category = Categories.objects.all().order_by('id')
    course = Course.objects.filter(status = 'PUBLISH').order_by('-id')
    for c in course:
        total_duration = Video.objects.filter(course=c).aggregate(total=Sum('time_duration'))['total'] or 0
        hours = total_duration // 60
        minutes = total_duration % 60
        formatted_duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        c.total_duration = formatted_duration

    context = {
        'category':category,
        'course':course,
    }
    return render(request, 'main/home.html',context)


def SINGLE_COURSE(request):
    category = Categories.get_all_category(Categories)
    level = Level.objects.all()
    course = Course.objects.all()
    FreeCourse_count = Course.objects.filter(price = 0).count()
    PaidCourse_count = Course.objects.filter(price__gte = 1).count()
    context = {
        'category':category,
        'level':level,
        'course':course,
        'FreeCourse_count':FreeCourse_count,
        'PaidCourse_count':PaidCourse_count,
    }
    return render(request, 'main/single_course.html',context)


def filter_data(request):
    category = request.GET.getlist('category[]')
    level = request.GET.getlist('level[]')
    price = request.GET.getlist('price[]')
    if price == ['PriceFree']:
        course = Course.objects.filter(price=0)
    elif price == ['PricePaid']:
        course = Course.objects.filter(price__gte=1)
    elif price == ['PriceAll']:
        course = Course.objects.all()
    elif category:
        course = Course.objects.filter(category__id__in = category).order_by('-id')
    elif level:
        course = Course.objects.filter(level__id__in = level).order_by('-id')
    else:
        course = Course.objects.all().order_by('-id')

    context = {
        'course':course,
    }

    t = render_to_string('ajax/course.html',context)
    return JsonResponse({'data': t})


def CONTACT_US(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if not name or not email or not message:
            messages.error(request, 'All fields are required!')
            return redirect('contact_us')

        contact = ContactUs(
            name=name,
            email=email,
            message=message,
        )
        contact.save()
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('contact_us')
    return render(request, 'main/contact_us.html')


def ABOUT_US(request):
    return render(request, 'main/about_us.html')


def SEARCH_COURSE(request):
    category = Categories.get_all_category(Categories)

    context = {
        'category':category,
    }
    query = request.GET['query']
    course = Course.objects.filter(title__icontains = query)
    
    context = {
        'course':course,
    }
    return render(request,'search/search.html',context)


def COURSE_DETAILS(request, slug):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first')
        return redirect('login')
    category = Categories.get_all_category(Categories)
    time_duration = Video.objects.filter(course__slug = slug).aggregate(sum = Sum('time_duration'))

    course = Course.objects.get(slug = slug)
    reviews = CourseReview.objects.filter(course = course, rating__in=[4, 4.5, 5]).order_by('-date')
    course_rating_average = CourseReview.objects.filter(course=course).aggregate(average_rating=Sum('rating') / Count('id'))['average_rating'] or 0

    one_star = CourseReview.objects.filter(course=course, rating__in=[0.5, 1]).count()
    two_star = CourseReview.objects.filter(course=course, rating__in=[1.5, 2]).count()
    three_star = CourseReview.objects.filter(course=course, rating__in=[2.5, 3]).count()
    four_star = CourseReview.objects.filter(course=course, rating__in=[3.5, 4]).count()
    five_star = CourseReview.objects.filter(course=course, rating__in=[4.5, 5]).count()

    total_reviews = one_star + two_star + three_star + four_star + five_star
    # Avoid division by zero
    if total_reviews > 0:
        one_star_percent = (one_star / total_reviews) * 100
        two_star_percent = (two_star / total_reviews) * 100
        three_star_percent = (three_star / total_reviews) * 100
        four_star_percent = (four_star / total_reviews) * 100
        five_star_percent = (five_star / total_reviews) * 100
    else:
        one_star_percent = two_star_percent = three_star_percent = four_star_percent = five_star_percent = 0

    if request.method == 'POST':
        if not(request.user.first_name and request.user.last_name):
            messages.error(request, 'Please complete your profile before leaving a review.')
            return redirect('profile')

        rating = request.POST.get('rating')
        title = request.POST.get('title')
        content = request.POST.get('content')

        comment = CourseReview(
            user=request.user,
            course=course,
            rating=float(rating) if rating else 0,
            title=title,
            content=content
        )
        comment.save()
        messages.success(request, 'Comment added successfully!')
        
    try:
        check_enroll = UserCourse.objects.get(user = request.user, course = course)
    except UserCourse.DoesNotExist:
        check_enroll = None

    latest_courses = Course.objects.filter(status = 'PUBLISH').order_by('-id')[:5]
    
    context = {
        'course':course,
        'category':category,
        'time_duration':time_duration,
        'latest_courses': latest_courses,
        'check_enroll':check_enroll,
        'reviews': reviews,
        'course_rating_average': round(course_rating_average, 2),
        'one_star': one_star,
        'two_star': two_star,
        'three_star': three_star,
        'four_star': four_star,
        'five_star': five_star,
        'one_star_percent': one_star_percent,
        'two_star_percent': two_star_percent,
        'three_star_percent': three_star_percent,
        'four_star_percent': four_star_percent,
        'five_star_percent': five_star_percent,
    }
    return render(request,'course/course_details.html',context)


def PAGE_NOT_FOUND(request):
    category = Categories.get_all_category(Categories)

    context = {
        'category':category,
    }
    return render(request,'error/404.html',context)


def CHECKOUT(request,slug):
    course = Course.objects.get(slug = slug)
    action = request.GET.get('action')
    order = None
    if course.price == 0:
        course = UserCourse(
            user = request.user,
            course = course,
        )
        course.save()
        messages.success(request, 'Enrolled in Course successfully')
        return redirect('my_course')
    
    elif action == 'create_payment':
        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')

            amount_cal = course.price - (course.price * course.discount / 100)
            amount_cal = amount_cal + (amount_cal * 0.18)  # Adding 18% tax
            amount = int(amount_cal) * 100
            currency = "INR"
            notes = {
                "name": f'{first_name} {last_name}',
                "email": email
            }
            receipt = f"Indeed-{int(time())}"
            order = client.order.create(
                {
                    'receipt': receipt,
                    'notes': notes,
                    'amount': amount,
                    'currency': currency,
                }
            )
            payment = Payment(
                course = course,
                user = request.user,
                order_id = order.get('id')
            )
            payment.save()
            return JsonResponse({
                "order_id": order.get("id"),
                "amount": amount,
                "course_title": course.title,
                "notes": notes,
            })
    
    context = {
        'course': course,
        'order': order,

    }
    return render(request,'checkout/checkout.html', context)


def MY_COURSE(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first')
        return redirect('login')

    category = Categories.objects.all().order_by('id')
    course = UserCourse.objects.filter(user = request.user)
    for c in course:
        total_duration = Video.objects.filter(course=c.course).aggregate(total=Sum('time_duration'))['total'] or 0
        hours = total_duration // 60
        minutes = total_duration % 60
        formatted_duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        c.total_duration = formatted_duration

    context = {
        'course':course,
        'category':category,
    }
    return render(request, 'course/my-course.html', context)


# @csrf_exempt
# def VERIFY_PAYMENT(request):
#     if request.method == 'POST':
#         data = request.POST
#         try:
#             client.utility.verify_payment_signature(data)
#             razorpay_order_id = data['razorpay_order_id']
#             razorpay_payment_id = data['razorpay_order_id']

#             payment = Payment.objects.get(order_id = razorpay_order_id)
#             payment.payment_id = razorpay_payment_id
#             payment.status = True

#             usercourse = UserCourse(
#                 user = payment.user,
#                 course = payment.course,
#             )
#             usercourse.save()
#             payment.user_course = usercourse
#             payment.save()

#             context = {
#                 'data': data,
#                 'payment': payment,
#             }
#             return render(request, 'verify_payment/success.html', context)
#         except:
#             return render(request, 'verify_payment/fail.html')


@csrf_exempt
def VERIFY_PAYMENT(request):
    if request.method == "POST":
        data = request.POST
        try:
            params_dict = {
                'razorpay_order_id': data.get('razorpay_order_id'),
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature': data.get('razorpay_signature'),
            }

            # Proper signature verification
            client.utility.verify_payment_signature(params_dict)

            razorpay_order_id = params_dict['razorpay_order_id']
            razorpay_payment_id = params_dict['razorpay_payment_id']

            payment = Payment.objects.get(order_id=razorpay_order_id)
            payment.payment_id = razorpay_payment_id
            payment.status = True

            # Create user-course relationship
            usercourse = UserCourse.objects.create(
                user=payment.user,
                course=payment.course,
            )

            payment.user_course = usercourse
            payment.save()

            context = {
                'data': data,
                'payment': payment,
            }
            return render(request, 'verify_payment/success.html', context)

        except razorpay.errors.SignatureVerificationError as e:
            # If signature mismatch or any other verification error
            return render(request, 'verify_payment/fail.html', {'error': str(e)})

        except Payment.DoesNotExist:
            # Order not found in your DB
            return render(request, 'verify_payment/fail.html', {'error': 'Payment record not found'})

        except Exception as e:
            # Any other unexpected error
            return render(request, 'verify_payment/fail.html', {'error': str(e)})

    return render(request, 'verify_payment/fail.html', {'error': 'Invalid request method'})

        

def WATCH_COURSE(request, slug):
    course = Course.objects.filter(slug = slug)
    lecture = request.GET.get('lecture')
    next = request.GET.get('next')
    previous = request.GET.get('previous')
    is_first_video = False
    is_last_video = False

    if course.exists():
        course = course.first()
    else:
        return redirect('404')

    if lecture:
        check_lecture = 1
        if int(lecture) != 1:
            check_lecture = int(lecture) - 1
        video = Video.objects.filter(serial_number=check_lecture, course=course).first()
        video_progress = VideoProgress.objects.filter(user=request.user, video=video).first()
        if video_progress == None or video_progress.completed == False:
            messages.error(request, 'Please complete videos in sequence fully before moving to the next.')
            previous_url = request.META.get('HTTP_REFERER')
            return redirect(previous_url)

    if lecture is None:
        lecture=1
    if next:
        video = Video.objects.filter(serial_number=next, course=course).first()
        video_progress = VideoProgress.objects.filter(user = request.user, video=video).first()
        if video_progress == None or video_progress.completed == False:
            messages.error(request, 'Please complete current video fully before moving to the next.')
            previous_url = request.META.get('HTTP_REFERER')
            return redirect(previous_url)
        lecture = int(next) + 1
    if previous:
        lecture = int(previous) - 1

    video = Video.objects.filter(serial_number=lecture, course=course).first()

    last_video = Video.objects.filter(course=course).order_by('-serial_number').first()
    is_last_video = video.id == last_video.id
    is_first_video = video.serial_number == 1

    comments = Comments.objects.filter(video=video, rating__in=[4, 4.5, 5]).order_by('-date')

    if request.method == 'POST':
        if not(request.user.first_name and request.user.last_name):
            messages.error(request, 'Please complete your profile before leaving a review.')
            return redirect('profile')
        
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        content = request.POST.get('content')

        comment = Comments(
            user=request.user,
            video=video,
            rating=float(rating) if rating else 0,
            title=title,
            content=content
        )
        comment.save()
        messages.success(request, 'Comment added successfully!')
    
    context = {
        'course':course,
        'video':video,
        'comments':comments,
        'is_first_video':is_first_video,
        'is_last_video':is_last_video,
    }
    return render(request, 'course/watch-course.html', context)


@csrf_exempt
def save_video_progress(request):
    if request.method == "POST":
        data = json.loads(request.body)
        video_id = data.get("video_id")
        seconds_watched = float(data.get("seconds_watched", 0))
        completed = data.get("completed", False)
        video_duration = float(data.get("video_duration", 0))

        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return JsonResponse({"error": "Video not found"}, status=404)

        progress, _ = VideoProgress.objects.get_or_create(
            user=request.user,
            video=video,
        )

        # Update only if watched time increased
        if seconds_watched > progress.watched_seconds:
            progress.watched_seconds = seconds_watched

        if completed:
            if video_duration:
                print('video duration:', video_duration)
                min_required_time = video_duration / 2
                print('min required duration:', min_required_time)
                print(progress.watched_seconds)
                print(progress.watched_seconds >= min_required_time)

                if progress.watched_seconds >= min_required_time:
                    progress.completed = True
                else:
                    return JsonResponse({
                        "status": "incomplete",
                        "message": (
                            "Please watch the full video without skipping to mark this as complete "
                            "and proceed to the next video."
                        )
                    })
            else:
                # If duration not known, fallback: mark complete
                progress.completed = True

        progress.save()

        if progress.completed == True:
            return JsonResponse({"status": "completed"})
        else:
            return JsonResponse({"status": "ok"})
    
    return JsonResponse({"error": "Invalid method"}, status=400)

# ------------ Blog Details Page ------------>

def blog_detail(request):
    return render(request, 'main/home_content/blog_details.html')


# def blog_detail(request, slug):
#     blog = get_object_or_404(Blog, slug=slug)

#     # Get related & trending posts
#     trending_posts = Blog.objects.order_by('-views')[:5]
#     related_posts = Blog.objects.filter(category=blog.category).exclude(id=blog.id)[:2]

#     return render(request, 'main/home_content/blog_details.html', {
#         'blog': blog,
#         'trending_posts': trending_posts,
#         'related_posts': related_posts,
#     })