from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login, name="auth_login"),
    path("register/", views.register, name="auth_register"),
    path("logout/", views.logout, name="auth_logout"),
]
