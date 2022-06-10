from django.conf import settings


def global_vars(request):
    return {
        "SEO_NOINDEX": settings.SEO_NOINDEX,
    }
