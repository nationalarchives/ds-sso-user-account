from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, TemplateView


class CommonContextMixin:
    title = ""
    main_heading = ""

    def get_title(self):
        return self.title

    def get_main_heading(self):
        return self.main_heading or self.get_title()

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            title=self.get_title(),
            main_heading=self.get_main_heading(),
            user=self.request.user,
            **kwargs
        )


class AccountDashboardView(LoginRequiredMixin, CommonContextMixin, TemplateView):
    title = "Manage your account"
    template_name = "patterns/pages/user/dashboard.html"


class VerifyEmailView(LoginRequiredMixin, CommonContextMixin, TemplateView):
    title = "Verify your email address"
    template_name = "patterns/pages/user/verify_email.html"


class UpdateDetailsView(LoginRequiredMixin, CommonContextMixin, FormView):
    title = "Update your details"
    template_name = "patterns/pages/user/update_details.html"


class ChangePasswordView(LoginRequiredMixin, CommonContextMixin, FormView):
    title = "Change your password"
    template_name = "patterns/pages/user/change_password.html"
