from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, TemplateView


class AccountDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "patterns/pages/user/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['title'] = 'Manage your account'
        context['user'] = user
        return context


class VerifyEmailView(LoginRequiredMixin, TemplateView):
    template_name = "patterns/pages/user/verify_email.html"


class UpdateDetailsView(LoginRequiredMixin, FormView):
    template_name = "patterns/pages/user/update_details.html"


class ChangePasswordView(LoginRequiredMixin, FormView):
    template_name = "patterns/pages/user/change_password.html"
