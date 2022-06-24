import logging

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from tna_account_management.users import forms

logger = logging.getLogger(__name__)


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
            **kwargs,
        )

class NonSocialLoginRequiredMixin(LoginRequiredMixin):
    social_user_redirect_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_social:
            messages.success(request, "Sorry, this information is automatically updated to match your social profile, and cannot be updated here.")
            return redirect(str(self.social_user_redirect_url))
        return super().dispatch(request, *args, **kwargs)


class AccountDashboardView(LoginRequiredMixin, CommonContextMixin, TemplateView):
    title = "Manage your account"
    template_name = "patterns/pages/user/dashboard.html"


class VerifyEmailView(LoginRequiredMixin, CommonContextMixin, FormView):
    title = "Verify your email address"
    form_class = forms.VerifyEmailForm
    template_name = "patterns/pages/user/verify_email.html"
    success_url = reverse_lazy("dashboard")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {'user_email': self.request.user.email,}
        )
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        try:
           user.resend_verification_email()
        except Exception:
            logger.exception(f"Failed to send verification email.")
            form.add_error(
                None,
                f"Failed to send verification email to {user.email}. Please wait a moment, then try again.",
            )
            return self.form_invalid(form)
        messages.success(
            self.request, "An email will be sent to you shortly."
        )
        return super().form_valid(form)


class UpdateNameView(NonSocialLoginRequiredMixin, CommonContextMixin, FormView):
    title = "Update your name"
    form_class = forms.NameForm
    template_name = "patterns/pages/user/update_name.html"
    success_url = reverse_lazy("dashboard")

    def get_initial(self):
        return {
            "name": self.request.user.name,
        }

    def form_valid(self, form):
        user = self.request.user
        try:
           user.update_name(form.cleaned_data["name"])
        except Exception:
            logger.exception("Failed to save changes to Auth0")
            form.add_error(
                None,
                "Failed to save changes. Please wait a moment, then try again.",
            )
            return self.form_invalid(form)
        messages.success(
            self.request, "Your name was changed successfully."
        )
        return super().form_valid(form)


class UpdateAddressView(LoginRequiredMixin, CommonContextMixin, FormView):
    title = "Update your address"
    form_class = forms.AddressForm
    template_name = "patterns/pages/user/update_address.html"
    success_url = reverse_lazy("dashboard")

    def get_initial(self):
        current = self.request.user.address
        if current is not None:
            return current.get_form_data()
        return {}

    def form_valid(self, form):
        user = self.request.user
        is_deletion = "delete" in self.request.POST
        try:
            if is_deletion:
                user.delete_address()
            else:
                user.update_address(form.cleaned_data)
        except Exception:
            logger.exception("Failed to save changes to Auth0")
            form.add_error(
                None,
                "Failed to save changes. Please wait a moment, then try again.",
            )
            return self.form_invalid(form)

        messages.success(
            self.request, "Your address was changed successfully."
        )
        return super().form_valid(form)


class ChangeEmailView(NonSocialLoginRequiredMixin, CommonContextMixin, FormView):
    title = "Change your email"
    form_class = forms.EmailForm
    template_name = "patterns/pages/user/change_email.html"
    success_url = reverse_lazy("auth_login")

    def form_valid(self, form):
        user = self.request.user

        # We have to perform this validation here, as the form
        # does not have access to user details
        if not user.check_password(form.cleaned_data["password"]):
            form.add_error("password", "The password you entered was invalid.")
            return self.form_invalid(form)

        try:
            user.update_email(form.cleaned_data["email"])
        except Exception:
            logger.exception("Failed to save changes to Auth0")
            form.add_error(
                None,
                "Failed to save changes. Please wait a moment, then try again.",
            )
            return self.form_invalid(form)

        # log the user out - they must log back in with their new email
        auth_logout(self.request)

        # redirect to login view
        return super().form_valid(form)


class ChangePasswordView(NonSocialLoginRequiredMixin, CommonContextMixin, FormView):
    title = "Change your password"
    template_name = "patterns/pages/user/change_password.html"
    success_url = reverse_lazy("dashboard")
