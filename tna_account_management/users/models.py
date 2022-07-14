import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.functional import cached_property

from tna_account_management.utils import auth0


class UnsupportedForUser(Exception):
    pass


class User(AbstractUser):
    auth0_id = models.CharField(max_length=36, blank=True, null=True, unique=True)

    @cached_property
    def profile(self) -> Dict[str, Any]:
        """
        Returns the profile data for this user from Auth0. Or, if the user is
        not connected to an Auth0 user, a blank dict.

        NOTE: This is a cached_property, so is 'setable'. Utilize this in tests
        to set dummy profile data and avoid calls to Auth0.
        """
        if self.auth0_id:
            return auth0.users_client.get(id=self.auth0_id)
        return {}

    def set_username(self, base: Optional[str] = None) -> None:
        """
        Set the 'username' model field value to a unique value, using the
        supplied value as a base, adding numbers to the end as necessary
        to ensure uniqueness.
        """
        base = base or self.profile.get("nickname")
        new_username = self._get_unique_username(base, self.pk)
        if not self.username or self.username != new_username:
            self.username = new_username

    @classmethod
    def _get_unique_username(cls, base: str, exclude_pk: int = None) -> str:
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
    def email(self) -> str:
        return self.profile.get("email", "")

    @cached_property
    def name(self) -> str:
        name = self.profile.get("name", "")
        if name == self.email:
            # Auth0 uses email as a placeholder when there is no name
            # specified, but we don't want that substitution here
            return ""
        return name

    @cached_property
    def name_segments(self) -> str:
        return self.name.strip().split(" ")

    @property
    def first_name(self) -> str:
        if given_name := self.profile.get("given_name"):
            return given_name
        if self.name:
            return self.name_segments[0]
        return self.username

    @property
    def last_name(self) -> str:
        if family_name := self.profile.get("family_name"):
            return family_name
        try:
            return " ".join(self.name_segments[1:])
        except IndexError:
            return ""

    @property
    def email_verified(self):
        return self.profile.get("email_verified", False)

    @property
    def is_social(self):
        return self.auth0_id and not self.auth0_id.startswith("auth0|")

    @property
    def auth0_db(self) -> Union[str, None]:
        for item in self.profile.get("identities", ()):
            if not item.get("isSocial", True):
                return item.get("connection")

    @cached_property
    def address(self) -> Union["Address", None]:
        addresses = self.profile.get("user_metadata", {}).get("addresses", ())
        try:
            return Address.from_auth0_json(addresses[0])
        except IndexError:
            return None

    def check_password(self, raw_password: str) -> bool:
        if self.has_usable_password():
            return super().check_password(raw_password)
        if db := self.auth0_db:
            return auth0.check_credentials(self.email, raw_password, db)
        return UnsupportedForUser

    def resend_verification_email(self):
        if not self.auth0_id:
            raise UnsupportedForUser
        auth0.jobs_client.send_verification_email(user_id=self.auth0_id)

    def update_name(self, new_name: str) -> None:
        if not self.auth0_id:
            raise UnsupportedForUser
        if self.name == new_name:
            return None
        auth0.users_client.update(self.auth0_id, {"name": new_name or self.email})
        self.name = new_name

    def update_email(self, new_email: str):
        if not self.auth0_id:
            raise UnsupportedForUser
        if self.email == new_email:
            return None
        auth0.users_client.update(self.auth0_id, {"email": new_email})
        self.email = new_email

    def update_password(self, raw_password: str):
        if self.auth0_id:
            auth0.users_client.update(self.auth0_id, {"password": raw_password})
        else:
            self.set_password(raw_password)
            self.save(update_fields=["password"])

    def update_address(self, data: Dict[str, str]):
        if not self.auth0_id:
            return UnsupportedForUser
        if self.address is None:
            self.address = Address()
        self.address.update(**data)
        auth0.users_client.update(
            self.auth0_id, {"user_metadata": {"addresses": [self.address.to_json()]}}
        )

    def delete_address(self):
        if not self.auth0_id or not self.address:
            return None
        self.address = None
        auth0.users_client.update(self.auth0_id, {"user_metadata": {"addresses": []}})


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
    def from_auth0_json(cls, data: Dict[str, Union[str, int]]):
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
