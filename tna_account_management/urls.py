"""tna_account_management URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("tna_account_management.authentication.urls")),
]


def trigger_error(request):
    # Raise a ZeroDivisionError
    return 1 / 0


if settings.SENTRY_DEBUG_URL_ENABLED:
    # url is toggled via the SENTRY_DEBUG_URL_ENABLED .env var
    urlpatterns.append(path("sentry-debug/", trigger_error))


if apps.is_installed("debug_toolbar"):
    urlpatterns = [
        path("__debug__/", include("debug_toolbar.urls")),
    ] + urlpatterns


urlpatterns.append(path("", include("tna_account_management.users.urls")))
