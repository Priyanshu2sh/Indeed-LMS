from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode
from .models import Certificate
from django.conf import settings

import base64
from io import BytesIO

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent



def generate_custom_certificate(certificate):

    certificate = Certificate.objects.get(pk=certificate.pk)

    if settings.ENVIRONMENT == 'Local':
        url = "127.0.0.1:8000/certification/"+certificate.randrand,
    elif settings.ENVIRONMENT == 'Server':
        url = "lms.indeedinspiring.com/certification/"+certificate.randrand,
    
    
    data = {
    "name": certificate.user_course.user.first_name +' '+ certificate.user_course.user.last_name ,
    "course_name": certificate.user_course.course.title,
    "id": str(certificate.unique_id),
    "template": certificate.user_course.course.template,
    "url": url
    }
    # Generate the QR code
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=4, border=2)
    qr.add_data(data["url"])
    qr.make(fit=True)

    # Create a QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Resize the QR code image to fit the original image
    qr_image = qr_image.resize((150, 150))  # Adjust the size as needed

    # Draw the QR code on the original image

    # opens the image
    img = Image.open(data["template"])

    # creates a drawing canvas overlay
    # on top of the image
    draw = ImageDraw.Draw(img)

    # gets the font object from the
    # font file (TTF)
    font1 = ImageFont.truetype(
        str( BASE_DIR / 'fonts/calibrib.ttf'),
        50  # change this according to your needs
    )

    font2 = ImageFont.truetype(
        str(BASE_DIR /  'fonts/CrashNumberingGothic.ttf'),
        30  # change this according to your needs
    )

    max_width = 740  # Adjust this according to your underline width
    start_point = 620
    
    # Get the size of the name
    name_text_bbox = draw.textbbox((0, 0), data["name"], font=font1)
    name_width = name_text_bbox[2] - name_text_bbox[0]
    y_pos = 655
    
    if name_width > max_width:
        while name_width > max_width:
            font_size = font1.size - 2  # Reduce font size
            y_pos = y_pos + 1
            font1 = ImageFont.truetype(str('fonts/calibrib.ttf'), font_size)
            name_text_bbox = draw.textbbox((0, 0), data["name"], font=font1)
            name_width = name_text_bbox[2] - name_text_bbox[0]
    
    padding = max_width - name_width
    padding_each_side = padding / 2


    # name on certificate
    draw.text(
        (
            start_point+padding_each_side,    # x-pos
            y_pos,   # y-pos
        ),
        data["name"],
        font=font1,
        fill="#262626")

    # Get the size of the course name
    course_max_width = 800
    course_start_point = 1195
    course_name_text_bbox = draw.textbbox((0, 0), data["course_name"], font=font1)
    course_name_width = course_name_text_bbox[2] - course_name_text_bbox[0]
    y_pos = 740

    if course_name_width > course_max_width:
        while course_name_width > course_max_width:
            font_size = font1.size - 2  # Reduce font size
            y_pos = y_pos + 1
            font1 = ImageFont.truetype(str('fonts/calibrib.ttf'), font_size)
            course_name_text_bbox = draw.textbbox((0, 0), data["course_name"], font=font1)
            course_name_width = course_name_text_bbox[2] - course_name_text_bbox[0]

    padding = course_max_width - course_name_width
    padding_each_side = padding / 2

    # course name on certificate
    draw.text(
        (
            course_start_point+padding_each_side,    # x-pos
            y_pos,   # y-pos
        ),
        data["course_name"],
        font=font1,
        fill="#262626")

    # certificate id on certificate
    draw.text(
        (
            930,    # x-pos
            1135,    # y-pos
        ),
        data["id"],
        font=font2,
        fill="#333333")




    # Resize QR code (scale it down)
    qr_small = qr_image.resize((qr_image.width - 20, qr_image.height - 20))  # 50% smaller
    # Draw the QR code on the original image
    img.paste(qr_small, (915, 970))  # Adjust the position as needed

    # saves the image in png format
    # img.save(BASE_DIR / 'certificates/{}.png'.format(data["name"])) 
    # img.save(BASE_DIR / 'certificates/{}.png'.format(name)) 

    # certificate.certificate = img
    # certificate.save()
    return img


