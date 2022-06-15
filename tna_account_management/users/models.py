from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    auth0_id = models.CharField(max_length=36, blank=True, null=True, unique=True)
    email_verified = models.BooleanField(default=False)

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
