from .models import Categories

def category_context(request):
    categories = Categories.objects.all()
    return {
        'category': categories
    }
