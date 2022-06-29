from urllib.parse import quote_plus, urlencode, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from authlib.integrations.django_client import OAuth


PROVIDER_NAME = "auth0"

User = get_user_model()

oauth = OAuth()
oauth.register(
    PROVIDER_NAME,
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)


def login(request):
    callback_url = reverse("auth_authorize")
    if next := request.GET.get("next"):
        request.session["auth_success_url"] = next
    return oauth.auth0.authorize_redirect(
        request, request.build_absolute_uri(callback_url)
    )


def register(request):
    callback_url = reverse("auth_authorize")
    if next := request.GET.get("next"):
        request.session["auth_success_url"] = next
    return oauth.auth0.authorize_redirect(
        request, request.build_absolute_uri(callback_url), screen_hint="signup", prompt="login"
    )


def authorize(request):
    if success_url := request.session.get("auth_success_url"):
        parsed = urlparse(success_url)
        if parsed.netloc and parsed.netloc != request.META.get("HTTP_HOST"):
            success_url = settings.LOGIN_REDIRECT_URL
    else:
        success_url = settings.LOGIN_REDIRECT_URL

    token = oauth.auth0.authorize_access_token(request)
    user_info = token["userinfo"]
    auth0_id = user_info.get("sub")

    try:
        # First, try to find an existing user
        user = User.objects.get(auth0_id=auth0_id)
    except User.DoesNotExist:
        # Create a new user
        user = User(auth0_id=auth0_id, is_social=not auth0_id.startswith("auth0|"))
        user.set_unusable_password()

    # Ensure details are up-to-date
    user.update_from_profile()

    auth_login(
        request,
        user,
        backend="tna_account_management.authentication.auth0.backend.Auth0Backend",
    )
    return HttpResponseRedirect(success_url)


def logout(request):
    if request.method != "POST":
        return render(request, "patterns/pages/auth/logout_confirm.html")
    auth_logout(request)
    return redirect(
        f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL),
                "client_id": settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )


def logout_success(request):
    return render(request, "patterns/pages/auth/logout_success.html")
