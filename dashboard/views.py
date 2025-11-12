from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.views.decorators.http import require_POST
from app.models import *
import json


# Create your views here.
def dashboard(request):
    total_courses = Course.objects.count()
    total_authors = Author.objects.count()
    total_categories = Categories.objects.count()
    total_levels = Level.objects.count()
    total_enrolled_students = UserCourse.objects.count()
    return render(request, 'dashboard/dashboard.html', {
        'total_courses': total_courses,
        'total_authors': total_authors,
        'total_categories': total_categories,
        'total_levels': total_levels,
        'total_enrolled_students': total_enrolled_students,
    })

def courses(request):
    courses = Course.objects.all().prefetch_related('what_you_learn_set', 'requirements_set')
    categories = Categories.objects.all()
    levels = Level.objects.all()
    authors = Author.objects.all()
    languages = Language.objects.all()
    return render(request, 'dashboard/courses.html', {
        'courses': courses,
        'categories': categories,
        'levels': levels,
        'authors': authors,
        'languages': languages,
    })

def authors(request):
    authors = Author.objects.all()
    return render(request, 'dashboard/authors.html', {'authors': authors})

def categories(request):
    categories = Categories.objects.all().order_by("id")
    levels = Level.objects.all()  # Add this line
    return render(request, 'dashboard/categories.html', {
        'categories': categories,
        'levels': levels,  # Add this line
    })

def levels(request):
    levels = Level.objects.all()
    return render(request, 'dashboard/levels.html', {'levels': levels})

def languages(request):
    languages = Language.objects.all()
    return render(request, 'dashboard/languages.html', {'languages': languages})

def edit_course(request):
    if request.method == "POST":
        print("POST KEYS:", list(request.POST.keys()))
        course_id = request.POST.get("id")
        course = get_object_or_404(Course, id=course_id)

        # Debug received data
        print("Received POST data:")
        print("Title:", request.POST.get("title"))
        print("What You Learn JSON:", request.POST.get("what_you_learn"))
        print("Requirements JSON:", request.POST.get("requirements"))

        # Update basic course fields
        course.title = request.POST.get("title")
        course.category_id = request.POST.get("category")
        course.level_id = request.POST.get("level")
        course.author_id = request.POST.get("author")
        course.language_id = request.POST.get("language")
        course.description = request.POST.get("description")
        course.price = request.POST.get("price")
        course.discount = request.POST.get("discount")
        course.Deadline = request.POST.get("Deadline")
        course.status = request.POST.get("status")
        course.certificate = request.POST.get("certificate")
        course.assessment_type = request.POST.get("assessment_type")
        course.is_subscription = request.POST.get("is_subscription") == "True"
        course.featured_video = request.POST.get("featured_video")
        
        if "featured_image" in request.FILES:
            course.featured_image = request.FILES["featured_image"]

        if "template" in request.FILES:
            course.template = request.FILES["template"]

        course.save()

        # Update What_you_learn
        what_you_learn_json = request.POST.get("what_you_learn", "[]")
        try:
            what_you_learn_list = json.loads(what_you_learn_json)
            print("Successfully parsed What You Learn:", what_you_learn_list)
        except Exception as e:
            print("Error parsing What You Learn JSON:", e)
            what_you_learn_list = []
        
        # Remove old What_you_learn entries
        What_you_learn.objects.filter(course=course).delete()
        
        # Add new What_you_learn entries
        for point in what_you_learn_list:
            if point and point.strip():
                What_you_learn.objects.create(course=course, points=point.strip())

        # Update Requirements
        requirements_json = request.POST.get("requirements", "[]")
        try:
            requirements_list = json.loads(requirements_json)
            print("Successfully parsed Requirements:", requirements_list)
        except Exception as e:
            print("Error parsing Requirements JSON:", e)
            requirements_list = []
        
        # Remove old Requirements entries
        Requirements.objects.filter(course=course).delete()
        
        # Add new Requirements entries
        for point in requirements_list:
            if point and point.strip():
                Requirements.objects.create(course=course, points=point.strip())

        messages.success(request, "Course updated successfully!")
        return redirect('courses')

@require_POST
def delete_course(request):
    course_id = request.POST.get("id")
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.success(request, "Course deleted successfully!")
    return redirect('courses')

def edit_author(request):
    if request.method == "POST":
        author_id = request.POST.get("id")
        author = get_object_or_404(Author, id=author_id)
        author.name = request.POST.get("name")
        author.about_author = request.POST.get("about_author")
        if "author_profile" in request.FILES:
            author.author_profile = request.FILES["author_profile"]
        author.save()
        messages.success(request, "Author updated successfully!")
        return redirect('authors')
    else:
        return redirect('authors')

@require_POST
def delete_author(request):
    author_id = request.POST.get("id")
    author = get_object_or_404(Author, id=author_id)
    author.delete()
    messages.success(request, "Author deleted successfully!")
    return redirect('authors')

def edit_category(request):
    if request.method == "POST":
        category_id = request.POST.get("id")
        category = get_object_or_404(Categories, id=category_id)
        category.name = request.POST.get("name")
        category.icon = request.POST.get("icon")
        category.save()
        messages.success(request, "Category updated successfully!")
        return redirect('categories')
    else:
        # For GET, show edit form (optional, if you want to use a separate page)
        category_id = request.GET.get("id")
        category = get_object_or_404(Categories, id=category_id)
        return render(request, 'dashboard/edit_category.html', {'category': category})

def edit_level(request):
    if request.method == "POST":
        level_id = request.POST.get("id")
        level = get_object_or_404(Level, id=level_id)
        level.name = request.POST.get("name")
        level.save()
        messages.success(request, "Level updated successfully!")
        return redirect('categories')
    else:
        level_id = request.GET.get("id")
        level = get_object_or_404(Level, id=level_id)
        return render(request, 'dashboard/edit_level.html', {'level': level})

def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name")
        icon = request.POST.get("icon")
        Categories.objects.create(name=name, icon=icon)
        messages.success(request, "Category added successfully!")
        return redirect('categories')

@require_POST
def delete_category(request):
    category_id = request.POST.get("id")
    if not category_id:
        messages.error(request, "No category ID received!")
        return redirect("categories")

    category = get_object_or_404(Categories, id=category_id)
    category.delete()
    messages.success(request, "Category deleted successfully!")
    return redirect("categories")


def videos(request):
    videos = Video.objects.select_related('course', 'lesson').all()
    courses = Course.objects.all()
    lessons = Lesson.objects.all()
    return render(request, 'dashboard/videos.html', {
        'videos': videos,
        'courses': courses,
        'lessons': lessons,
    })
  
@require_POST
def add_lesson(request):
    try:
        course_id = request.POST.get("course_id")
        lesson_name = request.POST.get("lesson_name")

        if not course_id or not lesson_name:
            return JsonResponse({"success": False, "message": "Course and Lesson name are required."})

        course = get_object_or_404(Course, id=course_id)
        lesson = Lesson.objects.create(course=course, name=lesson_name)

        # Return JSON response for AJAX
        return JsonResponse({
            "success": True,
            "message": f"Lesson '{lesson.name}' added successfully!",
            "lesson": {
                "id": lesson.id,
                "name": lesson.name,
                "course_id": course.id,
                "course_title": course.title
            }
        })

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error adding lesson: {str(e)}"})
    
    
@require_POST
def add_video(request):
    try:
        serial_number = request.POST.get("serial_number")
        course_id = request.POST.get("course")
        lesson_id = request.POST.get("lesson")
        title = request.POST.get("title")
        youtube_link = request.POST.get("youtube_link")
        time_duration = request.POST.get("time_duration")
        preview = request.POST.get("preview") == "True"
        description = request.POST.get("description")
        resources = request.FILES.get("resources")
        thumbnail = request.FILES.get("thumbnail")

        if not course_id or not lesson_id or not title:
            messages.error(request, "Course, Lesson, and Title are required.")
            return redirect('videos')

        course = get_object_or_404(Course, id=course_id)
        lesson = get_object_or_404(Lesson, id=lesson_id)

        video = Video.objects.create(
            serial_number=serial_number,
            course=course,
            lesson=lesson,
            title=title,
            youtube_link=youtube_link,
            time_duration=time_duration,
            preview=preview,
            description=description,
            resources=resources,
            thumbnail=thumbnail
        )
        
        messages.success(request, "Video added successfully!")
        return redirect('videos')
            
    except Exception as e:
        messages.error(request, f"Error adding video: {str(e)}")
        return redirect('videos')

@require_POST
def edit_video(request):
    video_id = request.POST.get("id")
    video = get_object_or_404(Video, id=video_id)

    try:
        video.serial_number = request.POST.get("serial_number")
        video.title = request.POST.get("title")
        video.youtube_link = request.POST.get("youtube_link")
        video.time_duration = request.POST.get("time_duration")
        video.description = request.POST.get("description")
        video.preview = request.POST.get("preview") == "True"

        # Update course & lesson
        course_id = request.POST.get("course")
        lesson_id = request.POST.get("lesson")
        if course_id:
            video.course = get_object_or_404(Course, id=course_id)
        if lesson_id:
            video.lesson = get_object_or_404(Lesson, id=lesson_id)

        if "resources" in request.FILES:
            video.resources = request.FILES["resources"]
        if "thumbnail" in request.FILES:
            video.thumbnail = request.FILES["thumbnail"]

        video.save()
        messages.success(request, "Video updated successfully!")
        return redirect('videos')
            
    except Exception as e:
        messages.error(request, f"Error updating video: {str(e)}")
        return redirect('videos')

@require_POST
def delete_video(request):
    video_id = request.POST.get("id")
    video = get_object_or_404(Video, id=video_id)
    video.delete()
    messages.success(request, "Video deleted successfully!")
    return redirect('videos')

def add_course(request):
    if request.method == "POST":
        title = request.POST.get("title")
        category_id = request.POST.get("category")
        level_id = request.POST.get("level")
        author_id = request.POST.get("author")
        language_id = request.POST.get("language")
        description = request.POST.get("description")
        price = request.POST.get("price")
        discount = request.POST.get("discount")
        deadline = request.POST.get("Deadline")
        status = request.POST.get("status")
        certificate = request.POST.get("certificate")
        assessment_type = request.POST.get("assessment_type")
        is_subscription = request.POST.get("is_subscription") == "True"
        featured_video = request.POST.get("featured_video")
        featured_image = request.FILES.get("featured_image")
        template = request.FILES.get("template")

        # Parse what_you_learn and requirements from JSON
        what_you_learn_json = request.POST.get("what_you_learn", "[]")
        requirements_json = request.POST.get("requirements", "[]")
        try:
            what_you_learn_list = json.loads(what_you_learn_json)
        except Exception:
            what_you_learn_list = []
        try:
            requirements_list = json.loads(requirements_json)
        except Exception:
            requirements_list = []

        course = Course.objects.create(
            title=title,
            category_id=category_id,
            level_id=level_id,
            author_id=author_id,
            language_id=language_id,
            description=description,
            price=price,
            discount=discount,
            Deadline=deadline,
            status=status,
            certificate=certificate,
            assessment_type=assessment_type,
            is_subscription=is_subscription,
            featured_video=featured_video,
            featured_image=featured_image,
            template=template
        )

        # Save What_you_learn
        for point in what_you_learn_list:
            if point and str(point).strip():
                What_you_learn.objects.create(course=course, points=str(point).strip())

        # Save Requirements
        for point in requirements_list:
            if point and str(point).strip():
                Requirements.objects.create(course=course, points=str(point).strip())

        messages.success(request, "Course added successfully!")
        return redirect('courses')

def add_author(request):
    if request.method == "POST":
        name = request.POST.get("name")
        about_author = request.POST.get("about_author")
        author_profile = request.FILES.get("author_profile")
        Author.objects.create(
            name=name,
            about_author=about_author,
            author_profile=author_profile
        )
        messages.success(request, "Author added successfully!")
        return redirect('authors')



def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        # Debug logging to help diagnose login problems
        print(f"[admin_login] Attempting login for: {username}")
        print("[admin_login] Password provided:" , bool(password))
        user = authenticate(request, username=username, password=password)
        print("[admin_login] authenticate() returned:", user)
        if user is not None:
            if not user.is_active:
                print("[admin_login] User is inactive")
                messages.error(request, "Account is inactive. Contact admin.")
                return redirect('adminlogin')
            login(request, user)
            print("[admin_login] Login successful for:", user.email)
            return redirect('dashboard')
        else:
            # Provide a clearer message and log to server console
            print("[admin_login] Authentication failed for:", username)
            messages.error(request, "Invalid email or password.")
            return redirect('adminlogin')
    return render(request, 'dashboard/login.html')

def logout(request):
    auth_logout(request)
    return redirect('adminlogin')