from django.conf import settings
from django.utils.functional import cached_property

import requests

from auth0.v3.authentication import GetToken
from auth0.v3.management import Users, Roles
from auth0.v3.rest import RestClient
from auth0.v3.exceptions import Auth0Error


class TokenGeneratingRestClient(RestClient):
    """
    An improved version of ``auth0.v3.rest.RestClient`` that lazily generates
    a jwt token when needed, caches it, and automatically generates a new
    one when it expires.
    """

    @cached_property
    def access_token(self) -> str:
        """
        Generate a jwt token that this client can use to make requests.
        When the token eventually expires, the cached retur value can be
        cleared by calling clear_cached_access_token().
        """
        get_token = GetToken(settings.AUTH0_DOMAIN)
        result = get_token.client_credentials(
            settings.AUTH0_CLIENT_ID,
            settings.AUTH0_CLIENT_SECRET,
            f"https://{settings.AUTH0_DOMAIN}/api/v2/",
        )
        return result['access_token']

    def regenerate_access_token(self) -> None:
        """
        When Auth0 responds with a "401: Invalid Token", this method is
        used to generate a fresh jwt token that can be used to repeat the
        request.
        """
        self.__dict__.pop("access_token", None)
        return self.access_token

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
        Overrides RestClient.get() to retry with a fresh jwt token if the
        initial attempt fails with a "401: Invalid token" response.
        """
        try:
            headers = self.add_auth_header(headers)
            return super().get(url, params, headers)
        except Auth0Error as e:
            if e.status_code != 401:
                raise
            self.regenerate_access_token()
            return super().get(url, params, self.add_auth_header(headers))

    def post(self, url, data=None, headers=None):
        """
        Overrides RestClient.post() to retry with a fresh jwt token if the
        initial attempt fails with a "401: Invalid token" response.
        """
        try:
            return super().post(url, data, self.add_auth_header(headers))
        except Auth0Error as e:
            if e.status_code != 401:
                raise
            self.regenerate_access_token()
            return super().post(url, data, self.add_auth_header(headers))

    def patch(self, url, data=None):
        """
        Overrides RestClient.patch() to retry with a fresh jwt token if the
        initial attempt fails with a "401: Invalid token" response.
        """
        first_attempt = True
        while True:
            response = requests.patch(
                url, json=data, headers=self.get_base_headers(), timeout=self.options.timeout
            )
            if response.status_code == 401 and first_attempt:
                self.regenerate_access_token()
                first_attempt = False
            else:
                break
        return self._process_response(response)

    def put(self, url, data=None):
        """
        Overrides RestClient.patch() to retry with a fresh jwt token if the
        initial attempt fails with a "401: Invalid token" response.
        """
        first_attempt = True
        while True:
            response = requests.put(
                url, json=data, headers=self.get_base_headers(), timeout=self.options.timeout
            )
            if response.status_code == 401 and first_attempt:
                self.regenerate_access_token()
                first_attempt = False
            else:
                break
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


users_client = TokenGeneratingUsersClient(domain=getattr(settings, "AUTH0_DOMAIN", ""))

roles_client = TokenGeneratingRolesClient(domain=getattr(settings, "AUTH0_DOMAIN", ""))
