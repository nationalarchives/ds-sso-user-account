import re
from dataclasses import dataclass
from typing import Any, Dict, List, Union

from django.conf import settings
from django.db import models
from django.db import transaction
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property
from tna_account_management.utils import auth0


@dataclass
class Address:
    house_name_no: str
    street: str
    town: str
    country: str
    postcode: str
    id: int = 1
    address_type: int = 1
    county: str = ""
    recipient_name: str = ""
    title: str = ""
    first_name: str = ""
    last_name: str = ""
    telephone: str = ""

    @classmethod
    def from_auth0_json(cls, data: Dict[str, Union[str,int]]):
        kwargs = {
            "id": data.get("Id", 1),
            "address_type": data.get("AddressType", 1),
            "telephone": data.get("Telephone", "").strip(),
            "title": data.get("Title", "").strip(),
            "first_name": data.get("Firstname", "").strip(),
            "last_name": data.get("Lastname", "").strip(),
            "recipient_name": data.get("RecipientName", "").strip(),
            "house_name_no": data.get("HouseNameNo", "").strip(),
            "street": data.get("Street", "").strip(),
            "town": data.get("Town", "").strip(),
            "county": data.get("County", "").strip(),
            "country": data.get("Country", "").strip(),
            "postcode": data.get("Postcode", "").strip(),
        }
        return cls(**kwargs)

    def to_auth0_json(self):
        return {
            "Id": self.id,
            "AddressType": self.address_type,
            "RecipientName": self.name,
            "Title": self.title,
            "Firstname": self.first_name,
            "Lastname": self.last_name,
            "Telephone": self.telephone,
            "HouseNameNo": self.house_name_no,
            "Street": self.street,
            "Town": self.town,
            "County": self.county,
            "Postcode": self.postcode,
            "Country": self.country,
        }

    @property
    def name(self):
        # use new, combined value if available
        if self.recipient_name:
            return self.recipient_name
        # combine separate name values into one
        name_bits = []
        if self.title:
            name_bits.append(self.title)
        if self.first_name:
            name_bits.append(self.first_name)
        if self.last_name:
            name_bits.append(self.last_name)
        return " ".join(name_bits)

    @staticmethod
    def looks_like_house_number(value: str) -> bool:
        return bool(re.match(r"^[0-9]+\s{0,2}[a-zA-z]{0,2}$", value))

    @property
    def lines(self) -> List[str]:
        lines = [self.name]
        if self.looks_like_house_number(self.house_name_no):
            lines.append(f"{self.house_name_no} {self.street}")
        else:
            lines.append(self.house_name_no)
            lines.append(self.street)
        lines.append(self.town)
        if self.county:
            lines.append(self.county)
        lines.append(self.country)
        lines.append(self.postcode)
        if self.telephone:
            lines.append(f"Tel: {self.telephone}")
        return lines

    def get_form_data(self):
        return {
            "recipient_name": self.name,
            "house_name_no": self.house_name_no,
            "street": self.street,
            "town": self.town,
            "county": self.county,
            "country": self.country,
            "postcode": self.postcode,
            "telephone": self.telephone,
        }

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class User(AbstractUser):
    name = models.TextField(max_length=400, blank=True)
    auth0_id = models.CharField(max_length=36, blank=True, null=True, unique=True)
    email_verified = models.BooleanField(default=False)
    is_social = models.BooleanField(default=False)
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
    def auth0_connection(self) -> Union[str, None]:
        for item in self.profile.get("identities", ()):
            if not item.get("isSocial", True):
                return item.get("connection")

    def check_password(self, raw_password: str) -> bool:
        if self.has_usable_password():
            return super().check_password(raw_password)
        return auth0.check_credentials(self.email, raw_password, self.auth0_connection)

    def resend_verification_email(self):
        auth0.jobs_client.send_verification_email(user_id=self.auth0_id)

    @transaction.atomic
    def update_name(self, new_name: str) -> None:
        if new_name == self.name:
            return None
        self.name = new_name
        self.save(update_fields=["name"])
        if self.auth0_id:
            auth0.users_client.update(self.auth0_id, {"name": new_name or self.email})

    @transaction.atomic
    def update_email(self, new_email: str):
        # Assume the new email is not verified (if actually changing).
        # Auth0 can tell us otherwise the next time they log in
        self.email_verified = new_email.lower() == self.email.lower()
        self.email = new_email
        self.save(update_fields=["email", "email_verified"])
        if self.auth0_id:
            auth0.users_client.update(self.auth0_id, {"email": self.email})

    def update_password(self, raw_password: str):
        if self.auth0_id:
            auth0.users_client.update(self.auth0_id, {"password": raw_password})
        else:
            self.set_password(raw_password)
            self.save(update_fields=["password"])

    def update_address(self, data: Dict[str, str]):
        if not self.auth0_id:
            return None
        if self.address is None:
            self.address = Address()
        self.address.update(**data)
        auth0.users_client.update(self.auth0_id, {
            "user_metadata": {"addresses": [self.address.to_json()]}
        })

    def delete_address(self):
        if not self.auth0_id or not self.address:
            return None
        auth0.users_client.update(self.auth0_id, {
            "user_metadata": {"addresses": []}
        })

    @cached_property
    def address(self) -> Union[Address, None]:
        addresses = self.profile.get("user_metadata", {}).get("addresses", ())
        try:
            return Address.from_auth0_json(addresses[0])
        except IndexError:
            return None

    def update_from_profile(self) -> List[str]:
        """
        Updates this user's `email`, `name`, `email_verified` and `username`
        values to reflect the latest available profile data, and saves the
        changes to the database.

        Returns a list containing the names of any fields that were updated.
        """
        changed_fields = []

        profile = self.profile
        email = profile.get("email", "")
        name = profile.get("name", "")
        email_verified = profile.get("email_verified", False)
        nickname = profile.get("nickname")

        if name.lower() == email.lower():
            name = ""

        if not self.email or self.email != email:
            self.email = email
            changed_fields.append("email")

        if not self.name or self.name != name:
            self.name = name
            changed_fields.append("name")

        if not self.email_verified and email_verified:
            self.email_verified = True
            changed_fields.append("email_verified")

        if nickname and (not self.username or 'email' in changed_fields):
            new_username = self.get_unique_username(nickname, self.pk)
            if self.username != new_username:
                self.username = new_username
                changed_fields.append("username")

        if self._state.adding:
            self.save()
        elif changed_fields:
            self.save(update_fields=changed_fields)

        # clear cached_property value
        self.__dict__.pop("address", None)

        return changed_fields
