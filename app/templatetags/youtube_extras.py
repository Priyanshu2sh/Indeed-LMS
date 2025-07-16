# youtube_extras.py
from django import template
import re

register = template.Library()

@register.filter
def youtube_video_id(url):
    # Extract ID from short links:
    m = re.match(r'https?://youtu\.be/([^\?&]+)', url)
    if m:
        return m.group(1)
    # Or from watch?v=...
    m = re.match(r'.*v=([^\?&]+)', url)
    if m:
        return m.group(1)
    return ''
