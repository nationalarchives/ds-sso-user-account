from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout as auth_logout, login as auth_login
from django.http import HttpResponse
from django.shortcuts import redirect, render

from tbxforms.forms import BaseForm as HelperMixin
from tbxforms.layout import Button


class CrispyAuthenticationForm(HelperMixin, AuthenticationForm):
    @property
    def helper(self):
        fh = super().helper
        fh.layout.extend(
            [
                Button.primary(
                    name="submit",
                    type="submit",
                    value="Sign in",
                ),
            ]
        )
        return fh


def login(request):
    form = CrispyAuthenticationForm(data=request.POST or None)
    if request.POST and form.is_valid():
        auth_login(request, form.get_user())
        redirect_to = form.cleaned_data.get("next", settings.LOGIN_REDIRECT_URL)
        if redirect_to != settings.LOGIN_REDIRECT_URL:
            parsed = urlparse(redirect_to)
            if parsed.netloc and parsed.netloc != request.META.get("HTTP_HOST"):
                redirect_to = settings.LOGIN_REDIRECT_URL
        return redirect(redirect_to)
    return render(request, "patterns/pages/auth/login.html", {"form": form})


def register(request):
    return HttpResponse(content="This is a stub view")


def logout(request):
    if request.method != "POST":
        return render(request, "patterns/pages/auth/logout_confirm.html")
    auth_logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


def logout_success(request):
    return render(request, "patterns/pages/auth/logout_success.html")
