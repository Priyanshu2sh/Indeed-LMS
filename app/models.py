# from django.contrib.auth.models import User
from datetime import datetime
import random
from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
# Create your models here.

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=254, null=True, blank=True)
    last_name = models.CharField(max_length=254, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return self.user.email

class Categories(models.Model):
    icon = models.CharField(max_length=200,null=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
    
    def get_all_category(self):
        return Categories.objects.all().order_by('id')
    

class Author(models.Model):
    author_profile = models.ImageField(upload_to="Media/author")
    name = models.CharField(max_length=100, null=True)
    about_author = models.TextField()

    def __str__(self):
        return self.name


class Level(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Language(models.Model):
    language = models.CharField(max_length=100)

    def __str__(self):
        return self.language


class Course(models.Model):
    STATUS = (
        ('PUBLISH','PUBLISH'),
        ('DRAFT', 'DRAFT'),
    )

    featured_image = models.ImageField(upload_to="Media/featured_img",null=True)
    featured_video = models.CharField(max_length=300,null=True)
    title = models.CharField(max_length=500)
    created_at = models.DateField(auto_now_add=True)
    author = models.ForeignKey(Author,on_delete=models.CASCADE,null=True)
    category = models.ForeignKey(Categories,on_delete=models.CASCADE)
    level = models.ForeignKey(Level,on_delete=models.CASCADE,null=True)
    description = models.TextField()
    price = models.IntegerField(null=True,default=0)
    discount = models.IntegerField(null=True)
    language = models.ForeignKey(Language,on_delete=models.CASCADE,null=True)
    Deadline = models.CharField(max_length=100, null=True)
    slug = models.SlugField(default='', max_length=500, null=True, blank=True)
    status = models.CharField(choices=STATUS,max_length=100,null=True)
    certificate = models.CharField(choices=(('Yes', 'Yes'), ('No', 'No')), max_length=100, default='No')
    template = models.ImageField(null=True, upload_to="Media/certificate_templates")
    assessment_type = models.CharField(
        choices=(
            ('Day', 'Day'),
            ('Final', 'Final'),
            ('No', 'No'),
        ),
        max_length=20,
        default='No',
    )


    is_subscription = models.BooleanField(default=False)  # True = monthly subscription


    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("course_details", kwargs={'slug': self.slug})
    

def create_slug(instance, new_slug=None):
    slug = slugify(instance.title)
    if new_slug is not None:
        slug = new_slug
    qs = Course.objects.filter(slug=slug).order_by('-id')
    exists = qs.exists()
    if exists:
        new_slug = "%s-%s" % (slug, qs.first().id)
        return create_slug(instance, new_slug=new_slug)
    return slug


def pre_save_post_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = create_slug(instance)

pre_save.connect(pre_save_post_receiver, Course)


class What_you_learn(models.Model):
    course = models.ForeignKey(Course,on_delete=models.CASCADE)
    points = models.CharField(max_length=500)

    def __str__(self):
        return self.points
    
class Requirements(models.Model):
    course = models.ForeignKey(Course,on_delete=models.CASCADE)
    points = models.CharField(max_length=500)

    def __str__(self):
        return self.points
    

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name + " - " +self.course.title

class Video(models.Model):
    serial_number = models.IntegerField(null=True)
    thumbnail = models.ImageField(upload_to="Media/Yt_Thumbnail", null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    youtube_link = models.CharField(max_length=200, null=True, blank=True)
    time_duration = models.IntegerField(null=True)
    preview = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    resources = models.FileField(upload_to="Media/course_resources", null=True, blank=True)

class Comments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    rating = models.FloatField(null=True, default=0)
    title = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name + " - " + self.video.title


class UserCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    paid = models.BooleanField(default=0)
    date = models.DateTimeField(auto_now_add = True)
    completed = models.BooleanField(default=False)

    # NEW FIELDS
    is_active = models.BooleanField(default=True)  # To cancel/expire subscription
    next_billing_date = models.DateField(null=True, blank=True)

    # CERTIFICATE MANAGEMENT
    certificate_issued = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email + " - " + self.course.title


class Payment(models.Model):
    order_id = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    user_course = models.ForeignKey(UserCourse, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email + " - " + self.course.title
    
class ContactUs(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date.strftime('%B %d, %Y at %I:%M %p')}"
    
class CourseReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    rating = models.FloatField(null=True, default=0)
    title = models.TextField()
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.course.title} - {self.rating}"
    
class VideoProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    watched_seconds = models.FloatField(default=0)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'video')
        
        

class Post(models.Model):
    
    CATEGORY = (
        ('Business','Business'),
        ('Technology','Technology'),
        ('Entertainment','Entertainment'),
        ('Sports','Sports')
    )

    SECTION = (
        ('Featured','Featured'),
        ('Popular','Popular'),
        ('Latest','Latest'),
        ('Trending','Trending')
    )

    featured_image = models.ImageField(upload_to='Media/post_images')
    title = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(choices=CATEGORY, max_length=200)
    date = models.DateField(auto_now_add=True)
    content = models.TextField()
    slug = models.SlugField(max_length=500, null=True, blank=True, unique=True)
    section = models.CharField(choices=SECTION, max_length=200)
    date_posted = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.section:
            self.section = random.choice(self.SECTION)[0]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
def create_slug(instance, new_slug=None):
    slug = slugify(instance.title)
    if new_slug is not None:
        slug = new_slug
    qs = Post.objects.filter(slug=slug).order_by('-id')
    exists = qs.exists()
    if exists:
        new_slug = "%s-%s" % (slug, qs.first().id)
        return create_slug(instance, new_slug=new_slug)
    return slug

def pre_save_post_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = create_slug(instance)

pre_save.connect(pre_save_post_receiver, Post)


class Tag(models.Model):
    name = models.CharField(max_length=100)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class PostComments(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.first_name} on {self.post.title}"
    
class Assessment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    day_number = models.PositiveIntegerField(null=True, blank=True)  # Only for day-wise
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True, null=True)
    is_final = models.BooleanField(default=False)

    class Meta:
        ordering = ['day_number']

class MCQQuestion(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])

class UserAssessmentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    score = models.FloatField(default=0)
    correct = models.IntegerField(default=0)
    wrong = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'assessment')


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user} -> {self.course.title}"
    
class Certificate(models.Model):
    user_course = models.ForeignKey(UserCourse, on_delete=models.CASCADE)
    unique_id = models.CharField(max_length=8, unique=True)
    randrand = models.CharField(max_length=100)
    downloaded = models.BooleanField(default=False)

    def __str__(self):
        return self.user_course.user.email + ' - ' + self.user_course.course.title

    def save(self, *args, **kwargs):
        if self.user_course.course.certificate == 'No':
            print(f"The certificate for {self.user_course.user.email} - {self.user_course.course.title} could not be issued because the course is not eligible for certification.")
            return

        if not self.pk:  # Only generate the ID if it's a new instance
            # Generate the unique ID based on last two digits of the year, month, and serial number
            now = datetime.now()
            year = str(now.year)[-2:]  # Last two digits of the year
            month = str(now.month).zfill(2)  # Zero padding for single digit months

            # Find the highest serial number for the current year and month
            max_serial = Certificate.objects.filter( unique_id__startswith=year + month ).aggregate(models.Max('unique_id'))['unique_id__max']
            serial_number = int(max_serial[-4:]) + 1 if max_serial else 1

            # Format the serial number with leading zeros
            serial_number = str(serial_number).zfill(4)
            self.unique_id = year + month + serial_number
            big_random_integer = random.randint(1000000000,9999999999)
            self.randrand = str(self.user_course.user.first_name).strip()+'-'+str(self.user_course.user.last_name).strip()+'-'+str(big_random_integer)+str(self.unique_id)

            user_course = UserCourse.objects.get(id = self.user_course.id)
            user_course.certificate_issued = True
            user_course.save()

        super().save(*args, **kwargs)  # Call the original save method

class CourseEnquiry(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='enquiries')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # optional, for logged-in users
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Enquiry by {self.user.email} for {self.course.title}"