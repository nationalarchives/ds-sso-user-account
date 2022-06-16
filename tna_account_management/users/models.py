from functools import cached_property
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    name = models.TextField(max_length=400)
    auth0_id = models.CharField(max_length=36, blank=True, null=True, unique=True)
    email_verified = models.BooleanField(default=False)
    profile_override = models.JSONField(
        blank=True,
        default=None,
        help_text="When set, self.profile will return this value instead of fetching real profile data from Auth0.",
    )

    def get_full_name(self):
        return self.name

    @cached_property
    def name_segments(self):
        return self.name.strip().split(" ")

    @property
    def first_name(self) -> str:
        return self.name_segments[0]

    @property
    def last_name(self) -> str:
        try:
            return " ".join(self.name_segments[1:])
        except IndexError:
            return ""

    @classmethod
    def get_unique_username(cls, base: str, exclude_pk: int = None):
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
