import base64
from collections import defaultdict
from io import BytesIO
from time import time
from django.contrib import messages
from django.shortcuts import redirect, render
from app.models import *
from django.template.loader import render_to_string
from django.http import FileResponse, HttpResponse, JsonResponse
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Count
from django.conf.urls import handler404
import json
from datetime import datetime, timedelta
from .generate_certificate import generate_custom_certificate
import razorpay
from LMS.settings import *

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def BASE(request):
    return render(request, 'base.html')


def HOME(request):
    category = Categories.objects.all().order_by('id')
    course = Course.objects.filter(status = 'PUBLISH').order_by('-id')
    posts = Post.objects.filter().order_by('-id')
    for c in course:
        total_duration = Video.objects.filter(course=c).aggregate(total=Sum('time_duration'))['total'] or 0
        hours = total_duration // 60
        minutes = total_duration % 60
        formatted_duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        c.total_duration = formatted_duration
        
        c.is_wishlist = False
        if request.user.is_authenticated:
            wishlist = Wishlist.objects.filter(user=request.user, course=c)
            if wishlist:
                c.is_wishlist = True

    context = {
        'category':category,
        'course':course,
        'posts':posts,
    }
    return render(request, 'main/home.html',context)


def SINGLE_COURSE(request):
    category = Categories.get_all_category(Categories)
    level = Level.objects.all()
    # course = Course.objects.all().order_by('-id')
    
    sort_option = request.GET.get('sort', 'default')
    
    if sort_option == 'low':
        course = Course.objects.all().order_by('price')
    elif sort_option == 'high':
        course = Course.objects.all().order_by('-price')
    else:
        course = Course.objects.all().order_by('-id')  # Default newest first
    
    
    for c in course:
        print(c.price)
        total_duration = Video.objects.filter(course=c).aggregate(total=Sum('time_duration'))['total'] or 0
        hours = total_duration // 60
        minutes = total_duration % 60
        formatted_duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        c.total_duration = formatted_duration
        
        c.is_wishlist = False
        if request.user.is_authenticated:
            wishlist = Wishlist.objects.filter(user=request.user, course=c)
            if wishlist:
                c.is_wishlist = True

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
        return redirect('register')
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
        check_enroll = UserCourse.objects.get(user = request.user, course = course, is_active=True)
    except UserCourse.DoesNotExist:
        check_enroll = None

    latest_courses = Course.objects.filter(status = 'PUBLISH').order_by('-id')[:5]

    assessments = Assessment.objects.filter(course=course).order_by('day_number')
    for a in assessments:
        user_progress = UserAssessmentProgress.objects.filter(user=request.user, assessment=a).first()
        if user_progress:
            a.user_completed = user_progress.is_completed
            a.score = user_progress.score
            a.correct = user_progress.correct
            a.wrong = user_progress.wrong
        else:
            a.user_completed = False
            
    if request.user.is_authenticated:
        wishlist_courses = Course.objects.filter(wishlist__user=request.user)
    else:
        wishlist_courses = Course.objects.none()


    course_enquiry = CourseEnquiry.objects.filter(course=course, user=request.user).first()
    if not course_enquiry:
        course_enquiry = False
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
        'assessments': assessments,
        'request': request,
        'wishlist_courses': wishlist_courses,
        'course_enquiry': course_enquiry
    }
    return render(request,'course/course_details.html',context)


def PAGE_NOT_FOUND(request, exception):
    return render(request, 'error/404.html', status=404)

def CHECKOUT(request,slug):
    course = Course.objects.get(slug = slug)
    action = request.GET.get('action')
    order = None
    razorpay_key_id = settings.RAZORPAY_KEY_ID
    if settings.ENVIRONMENT == 'Local':
        callback_url = "http://127.0.0.1:8000/verify_payment"
    if settings.ENVIRONMENT == 'Server':
        callback_url = "http://127.0.0.1:8000/verify_payment"

    if course.price == 0:
        usercourse = UserCourse(
            user = request.user,
            course = course,
        )

        if course.is_subscription:
            usercourse.is_active = True
            usercourse.next_billing_date = datetime.now().date() + timedelta(days=30)
        usercourse.save()

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
        'razorpay_key_id': razorpay_key_id,
        'callback_url': callback_url,

    }
    return render(request,'checkout/checkout.html', context)

def MY_COURSE(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first')
        return redirect('register')

    selected_category = request.GET.get('category')
    search_query = request.GET.get('search', '').strip()

    # All enrolled courses
    all_user_courses = UserCourse.objects.filter(user=request.user).select_related('course')
    print("Total enrolled:", all_user_courses.count())

    # Get enrolled course categories
    category_ids = all_user_courses.values_list('course__category__id', flat=True).distinct()
    category = Categories.objects.filter(id__in=category_ids).order_by('id')

    # Apply combined filters
    if selected_category and selected_category.isdigit():
        all_user_courses = all_user_courses.filter(course__category__id=selected_category)
        print("After category filter:", all_user_courses.count())

    if search_query:
        print("Search query:", search_query)
        all_user_courses = all_user_courses.filter(course__title__icontains=search_query)
        print("After search filter:", all_user_courses.count())

    # Debug enrolled course titles
    for uc in all_user_courses:
        print("Matched course title:", uc.course.title)

    # Add total duration
    for c in all_user_courses:
        total_duration = Video.objects.filter(course=c.course).aggregate(total=Sum('time_duration'))['total'] or 0
        hours = total_duration // 60
        minutes = total_duration % 60
        c.total_duration = f"{hours}h {minutes}m" if hours else f"{minutes}m"

    context = {
        'course': all_user_courses,
        'category': category,
        'selected_category': int(selected_category) if selected_category and selected_category.isdigit() else None,
        'search_query': search_query,
    }

    return render(request, 'course/my-course.html', context)

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
            print(params_dict)

            # Proper signature verification
            client.utility.verify_payment_signature(params_dict)

            razorpay_order_id = params_dict['razorpay_order_id']
            razorpay_payment_id = params_dict['razorpay_payment_id']
            print(False)
            payment = Payment.objects.get(order_id=razorpay_order_id)
            print(payment)
            payment.payment_id = razorpay_payment_id
            payment.status = True

            # Create user-course relationship
            usercourse, _ = UserCourse.objects.get_or_create(
                user=payment.user,
                course=payment.course,
                
            )
            usercourse.paid=True

            if payment.course.is_subscription:
                usercourse.is_active = True
                usercourse.next_billing_date = datetime.now().date() + timedelta(days=30)

            usercourse.save()

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
            print(e)
            return render(request, 'verify_payment/fail.html', {'error': str(e)})

    return render(request, 'verify_payment/fail.html', {'error': 'Invalid request method'})



def WATCH_COURSE(request, slug):
    course = Course.objects.filter(slug=slug).first()
    if not course:
        return redirect('404')

    lecture = request.GET.get('lecture')
    next_param = request.GET.get('next')
    previous = request.GET.get('previous')
    is_first_video = False
    is_last_video = False

    # Fallback to lecture 1
    if lecture:
        lecture = int(lecture)
    elif next_param:
        lecture = int(next_param) + 1
    elif previous:
        lecture = int(previous) - 1
    else:
        lecture = 1

    # Get completed video serials
    completed_serials = list(
        VideoProgress.objects.filter(
            user=request.user,
            video__course=course,
            completed=True
        ).values_list('video__serial_number', flat=True)
    )

    all_video_serials = list(
        Video.objects.filter(course=course).values_list('serial_number', flat=True)
    )

    if lecture == 1:
        is_first_video = True
        if max(all_video_serials) == lecture:
            is_last_video = True

    # Prevent skipping — check previous video progress (for lecture & next clicks)
    if lecture > 1:
        prev_video = Video.objects.filter(serial_number=lecture - 1, course=course).first()
        prev_progress = VideoProgress.objects.filter(user=request.user, video=prev_video).first()
        if not prev_progress or not prev_progress.completed:
            messages.error(request, 'Please complete previous videos fully before moving ahead.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        is_first_video = prev_video.serial_number == 1
        last_video = Video.objects.filter(course=course).order_by('-serial_number').first()
        is_last_video = last_video and prev_video.id == last_video.id

        # ⚠️ Check if all videos completed and current video is last
        last_video_progress = VideoProgress.objects.filter(video=last_video, user=request.user).first()

        if (
            set(all_video_serials) == set(completed_serials) and
            prev_video == last_video and
            last_video_progress and last_video_progress.completed
        ):
            user_course = UserCourse.objects.filter(user=request.user, course=course).first()
            if user_course and not user_course.completed:
                user_course.completed = True
                user_course.save()

                print('qqqqqq')
                # Create certificate if not exists
                certificate, created = Certificate.objects.get_or_create(user_course=user_course)
                print('aaaaaaaaaaaa')
                if created:
                    generate_custom_certificate(certificate)

                messages.success(request, f'🎉 Congratulations! Your "{course.title}" course is now marked as completed!')
                return redirect('my_course')

            if user_course and user_course.completed:
                return redirect(request.META.get('HTTP_REFERER', '/'))


    # Load the video to be played
    video = Video.objects.filter(serial_number=lecture, course=course).first()

    if not video:
        messages.error(request, 'This video does not exist.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Handle review form POST
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if not (request.user.first_name and request.user.last_name):
            return JsonResponse({'status': 'error', 'message': 'Please complete your profile before leaving a review.'})

        rating = request.POST.get('rating')
        title = request.POST.get('title')
        content = request.POST.get('content')

        Comments.objects.create(
            user=request.user,
            video=video,
            rating=float(rating) if rating else 0,
            title=title,
            content=content
        )
        return JsonResponse({'status': 'success', 'message': 'Comment added successfully!'})

    comments = Comments.objects.filter(video=video, rating__in=[4, 4.5, 5]).order_by('-date')

    context = {
        'course': course,
        'video': video,
        'comments': comments,
        'is_first_video': is_first_video,
        'is_last_video': is_last_video,
        'completed_videos': completed_serials,
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
                min_required_time = video_duration / 2
                
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

def blog_detail(request, pk):
    post = Post.objects.get(id=pk)
    tags = Tag.objects.filter(post=post)
    comments = PostComments.objects.filter(post=post).order_by('-date')
    other_posts = Post.objects.all().exclude(id=post.id)[:5]
    return render(request, 'main/blog_details.html', {'post': post, "tags": tags, "comments": comments, "other_posts":other_posts})


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

def add_blog_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        
        if not request.user.is_authenticated:
            messages.error(request, 'Please login first!')
            return redirect('register')

        if not request.user.first_name or not request.user.last_name:
            messages.error(request, 'Please update your profile first!')
            return redirect('profile')
        
        content = request.POST.get('message') 
        if not content:
            messages.error(request, 'Please add valid comment!')
            return redirect('blog_detail', pk=post.id)

        PostComments.objects.create(
            post=post,
            user=request.user,
            content=content
        )
        messages.success(request, 'Comment added successfully')
        return redirect('blog_detail', pk=post.id)
    
 
def my_certificates(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first!')
        return redirect('register')
    user_course = UserCourse.objects.filter(user=request.user, completed=True, certificate_issued=True)
    return render(request, 'certificate/my_certificate.html', {'user_course': user_course})
    
def view_certificate(request, pk):
    user_course = UserCourse.objects.get(id=pk)
    certificate = Certificate.objects.get(user_course=user_course)
    img = generate_custom_certificate(certificate)

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')  # or 'JPEG' if that's your format
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'certificate/view_certificate.html', {'user_course': user_course, "certificate": certificate, 'img_base64': img_base64})
    
@login_required
def start_assessment(request, pk):
    assessment = get_object_or_404(Assessment, id=pk)
    previous_assessment_day = assessment.day_number - 1
    questions = assessment.questions.all()

    if previous_assessment_day > 0:
        # Check if user has already completed this assessment
        previous_result = UserAssessmentProgress.objects.filter(
            user=request.user, assessment__day_number=previous_assessment_day, is_completed=True
        ).first()
        if not previous_result:
            messages.error(request, "Please complete previous assessment first.")
            return redirect('course_details', slug=assessment.course.slug)


    if request.method == 'POST':
        total_questions = questions.count()
        correct_answers = 0

        for q in questions:
            user_answer = request.POST.get(f'question_{q.id}')
            if user_answer == q.correct_option:
                correct_answers += 1

        wrong_answers = total_questions - correct_answers
        score = round((correct_answers / total_questions) * 100, 2)

        # Save or update progress
        UserAssessmentProgress.objects.update_or_create(
            user=request.user,
            assessment=assessment,
            defaults={'is_completed': True, 'score': score,'correct': correct_answers,'wrong': wrong_answers}
        )

        messages.success(request, f"You completed the assessment with a score of {score}%")
        return redirect('course_details', slug=assessment.course.slug)  # redirect back

    return render(request, 'assessment/start_assessment.html', {
        'assessment': assessment,
        'questions': questions,
    })


def wishlist_view(request):
    wishlist_courses = Wishlist.objects.filter(user=request.user).select_related('course')
    return render(request, 'main/wishlist.html', {'wishlist_courses': wishlist_courses})

def add_to_wishlist(request, course_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first!')
        return redirect('register')
    course = get_object_or_404(Course, id=course_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, course=course)

    if not created:
        wishlist_item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def remove_from_wishlist(request, course_id):
    Wishlist.objects.filter(user=request.user, course_id=course_id).delete()
    messages.success(request, 'Course removed from wishlist.')
    return redirect('wishlist')




@login_required
def toggle_wishlist_ajax(request):
    course_id = request.POST.get('course_id')
    course = get_object_or_404(Course, id=course_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, course=course)

    if not created:
        wishlist_item.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})


def display_certificate(request, randrand):
    try:
        certificate = get_object_or_404(Certificate, randrand=randrand)
        
        # if certificate.course.certification_date is None:
        #     raise TypeError("Error: Certification date missing")
        
        generated_image = generate_custom_certificate(certificate)

        buffer = BytesIO()
        generated_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return FileResponse(buffer, content_type='image/png')
    except Exception as e:
        return HttpResponse(f"""
        <div style="text-align:center;margin:30px;">
        <p style="font-size:24px;">Certificate Not Found.</p>
        <p>{e}</p>
        </div>""")


def terms_and_conditions(request):
    return render(request, 'main/terms_and_conditions.html')

def privacy_policy(request):
    return render(request, 'main/privacy_policy.html')

def cancellation_refund(request):
    return render(request, 'main/cancellation_refund.html')

def shipping_exchange(request):
    return render(request, 'main/shipping_exchange.html')

def course_enquiry(request, slug):
    user = request.user
    course = get_object_or_404(Course, slug=slug)

    if request.method == 'POST':
        message = request.POST.get('message')
        if not message:
            messages.error(request, 'Please enter a message.')
            return redirect('course_enquiry', slug=slug)
        
        CourseEnquiry.objects.create(
            course=course,
            user=user,
            message=message
        )

        messages.success(request, 'Your enquiry has been submitted!')
        return redirect('course_details', slug=slug)

    return render(request, 'courses/course_enquiry.html', {'course': course})