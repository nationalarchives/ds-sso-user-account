from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, TemplateView


class AccountDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "patterns/user/dashboard.html"


class VerifyEmailView(LoginRequiredMixin, TemplateView):
    template_name = "patterns/user/verify_email.html"


class UpdateDetailsView(LoginRequiredMixin, FormView):
    template_name = "patterns/user/update_details.html"


class ChangePasswordView(LoginRequiredMixin, FormView):
    template_name = "patterns/user/change_password.html"
