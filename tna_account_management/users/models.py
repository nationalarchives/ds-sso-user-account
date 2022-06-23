from typing import Any, Dict, Sequence

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property
from tna_account_management.utils import auth0


class User(AbstractUser):
    name = models.TextField(max_length=400, blank=True)
    auth0_id = models.CharField(max_length=36, blank=True, null=True, unique=True)
    email_verified = models.BooleanField(default=False)
    profile_override = models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text="When set, self.profile will return this value instead of fetching real profile data from Auth0.",
    )

    @classmethod
    def get_unique_username(cls, base: str, exclude_pk: int = None) -> str:
        candidate_username = base[:150]
        username = candidate_username
        i = 1
        qs = User.objects.all()
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        while qs.filter(username=username).exists():
            username = f"{candidate_username[:148]}{i}"
            i += 1
        return username

    def get_full_name(self) -> str:
        return self.name or self.username

    @cached_property
    def name_segments(self) -> str:
        return self.name.strip().split(" ")

    @property
    def first_name(self) -> str:
        if self.name:
            return self.name_segments[0]
        return self.username

    @property
    def last_name(self) -> str:
        try:
            return " ".join(self.name_segments[1:])
        except IndexError:
            return ""

    @cached_property
    def profile(self) -> Dict[str, Any]:
        if self.profile_override is not None:
            return self.profile_override
        if self.auth0_id:
            return auth0.users_client.get(id=self.auth0_id)
        return {}

    @property
    def addresses(self) -> Sequence[Dict[str, Any]]:
        return self.profile.get("addresses", ())

    def set_email_verified_status(self) -> None:
        changed = False
        value_from_profile = self.profile.get("email_verified")
        if not self.email_verified and value_from_profile:
            self.email_verified = True
            changed = True
        elif self.email_verified and value_from_profile is False:
            self.email_verified = False
            changed = True
        if changed:
            self.save(update_fields=["email_verified"])
