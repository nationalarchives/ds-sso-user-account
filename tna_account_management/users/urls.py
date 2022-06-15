from django.urls import path

from . import views

urlpatterns = [
    path("update-details", views.UpdateDetailsView.as_view(), name="update_details"),
    path("verify-your-email", views.VerifyEmailView.as_view(), name="verify_email"),
    path("change-password", views.ChangePasswordView.as_view(), name="change_password"),
    path("", views.AccountDashboardView.as_view(), name="dashboard"),
]
