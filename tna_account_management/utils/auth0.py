from datetime import timedelta, datetime

from django.conf import settings
from django.utils.functional import cached_property

import requests

from auth0.v3.authentication import GetToken
from auth0.v3.exceptions import Auth0Error
from auth0.v3.management import Users, Roles, Jobs
from auth0.v3.rest import RestClient


def check_credentials(username: str, password: str, realm: str):
    get_token = GetToken(settings.AUTH0_DOMAIN)
    try:
        get_token.login(
            client_id=settings.AUTH0_CLIENT_ID,
            client_secret=settings.AUTH0_CLIENT_SECRET,
            audience=f"https://{settings.AUTH0_DOMAIN}/api/v2/",
            username=username,
            password=password,
            scope="",
            realm=realm,
        )
    except Auth0Error as e:
        if e.status_code == 403:
            return False
        raise e
    else:
        return True


class TokenGeneratingRestClient(RestClient):
    """
    An improved version of ``auth0.v3.rest.RestClient`` that lazily generates
    a jwt token when needed, caches it, and automatically generates a new
    one when it expires.
    """

    @property
    def access_token(self) -> str:
        """
        Generate a jwt token that this client can use to make requests.
        When the token eventually expires, the cached retur value can be
        cleared by calling clear_cached_access_token().
        """
        current_time = datetime.now()
        current_token = getattr(self, '_jwt_token', None)
        current_token_expiry = getattr(self, '_jwt_token_expiry', current_time)

        # Reuse the current token if it's still valid
        if current_token and (current_time + timedelta(seconds=5) < current_token_expiry):
            return current_token

        # There is not current token, or it will soon expire,
        # so generate a new one
        get_token = GetToken(settings.AUTH0_DOMAIN)
        result = get_token.client_credentials(
            settings.AUTH0_CLIENT_ID,
            settings.AUTH0_CLIENT_SECRET,
            f"https://{settings.AUTH0_DOMAIN}/api/v2/",
        )

        # Store the token for reuse
        self._jwt_token = result['access_token']

        # Caclulate a new expiry date, so that we know when to
        # generate a fresh token
        self._jwt_token_expiry = datetime.now() + timedelta(result["expires_in"])
        return self._jwt_token

    def add_auth_header(self, custom_headers):
        """
        When get() or post() are called, this method is used to add the
        'Authorization' header to any other custom headers passed to the
        method.
        """
        if not custom_headers:
            headers = {}
        else:
            headers = custom_headers.copy()
        headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def get_base_headers(self):
        """
        When patch() or put() are called, this method is used to get a copy
        of `self.base_headers` with the "Authorization" header added. The
        original patch() and put() methods do not accept a 'headers' argument,
        so cannot be overriden in the same way as get() and post().
        """
        return self.add_auth_header(self.base_headers)

    def get(self, url, params=None, headers=None):
        """
        Overrides RestClient.get() to ensure the 'Authentication' header
        is present.
        """
        return super().get(url, params, self.add_auth_header(headers))

    def post(self, url, data=None, headers=None):
        """
        Overrides RestClient.post() to ensure the 'Authentication' header
        is present.
        """
        return super().post(url, data, self.add_auth_header(headers))

    def patch(self, url, data=None):
        """
        Overrides RestClient.patch() to ensure the 'Authentication' header
        is present.
        """
        response = requests.patch(
            url, json=data, headers=self.get_base_headers(), timeout=self.options.timeout
        )
        return self._process_response(response)

    def put(self, url, data=None):
        """
        Overrides RestClient.patch() to ensure the 'Authentication' header
        is present.
        """
        response = requests.put(
            url, json=data, headers=self.get_base_headers(), timeout=self.options.timeout
        )
        return self._process_response(response)


class TokenGeneratingClient:

    target_api = ""

    def __init__(
        self,
        domain: str = settings.AUTH0_DOMAIN,
        telemetry: bool = True,
        timeout: float = 5.0,
        protocol: str = "https",
        rest_options=None,
    ):
        self.domain = domain
        self.telemetry = telemetry
        self.timeout = timeout
        self.protocol = protocol
        self.rest_options = rest_options

    @cached_property
    def client(self):
        return TokenGeneratingRestClient(
            jwt=None, telemetry=self.telemetry, timeout=self.timeout, options=self.rest_options
        )


class TokenGeneratingUsersClient(TokenGeneratingClient, Users):
    """
    A custom version of the `Users` client that lazily generates
    a jwt token when needed and automatically refreshes it and retries
    if it receives a "401: Invalid token" response from Auth0.
    """
    pass


class TokenGeneratingRolesClient(TokenGeneratingClient, Roles):
    """
    A custom version of the `Roles` client that lazily generates
    a jwt token when needed and automatically refreshes it and retries
    if it receives a "401: Invalid token" response from Auth0.
    """
    pass


class TokenGeneratingJobsClient(TokenGeneratingClient, Jobs):
    """
    A custom version of the `Jobs` client that lazily generates
    a jwt token when needed and automatically refreshes it and retries
    if it receives a "401: Invalid token" response from Auth0.
    """

    # Make the 'body' arg optional and just accept user_id instead so we
    # don't have to manually compose the body elsewhere.
    def send_verification_email(self, body=None, user_id=None):
        if (body is None) and user_id:
            body = {"user_id": user_id, "client_id": settings.AUTH0_CLIENT_ID}

        super().send_verification_email(body)


users_client = TokenGeneratingUsersClient(domain=getattr(settings, "AUTH0_DOMAIN", ""))

roles_client = TokenGeneratingRolesClient(domain=getattr(settings, "AUTH0_DOMAIN", ""))

jobs_client = TokenGeneratingJobsClient(domain=getattr(settings, "AUTH0_DOMAIN", ""))
