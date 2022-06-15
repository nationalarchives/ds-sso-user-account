from django.conf import settings

from .auth0 import urls as auth0_urls
from .django import urls as django_urls

urlpatterns = []

provider =  getattr(settings, "AUTHENTICATION_PROVIDER", "django")

if provider == 'auth0':
    urlpatterns.extend(auth0_urls.urlpatterns)
else:
    urlpatterns.extend(django_urls.urlpatterns)
