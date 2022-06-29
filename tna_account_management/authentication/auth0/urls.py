from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login, name="auth_login"),
    path("register/", views.register, name="auth_register"),
    path("logout/", views.logout, name="auth_logout"),
    path("logout/success/", views.logout_success, name="auth_logout_success"),
    path("authorize/", views.authorize, name="auth_authorize"),
]
