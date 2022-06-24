from django import forms
from django.core.exceptions import ValidationError

from tbxforms.forms import BaseForm as HelperMixin
from tbxforms.layout import Button


class VerifyEmailForm(HelperMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        self.user_email = kwargs.pop("user_email", None)
        super().__init__(*args, **kwargs)

    @property
    def helper(self):
        fh = super().helper
        fh.layout.extend([
            Button.primary(
                name="submit",
                type="submit",
                value=f"Resend email to {self.user_email}",
            ),
        ])
        return fh


class NameForm(HelperMixin, forms.Form):
    name = forms.CharField(max_length=200, required=False)

    @property
    def helper(self):
        fh = super().helper
        fh.layout.extend([
            Button.primary(
                name="submit",
                type="submit",
                value="Save changes",
            ),
        ])
        return fh


class AddressForm(HelperMixin, forms.Form):
    recipient_name = forms.CharField(max_length=255, help_text="For example: Mr John Smith")
    house_name_no = forms.CharField(label="House name or number", max_length=100)
    street = forms.CharField(max_length=200)
    town = forms.CharField(label="Town or City", max_length=100)
    county: forms.CharField(max_length=100, required=False)
    country = forms.CharField(max_length=100)
    postcode = forms.CharField(max_length=15)
    telephone = forms.CharField(max_length=100, required=False)

    @property
    def helper(self):
        fh = super().helper
        fh.layout.extend([
            Button.primary(
                name="submit",
                type="submit",
                value="Save changes",
            ),
            Button.secondary(
                name="delete",
                type="submit",
                value="Delete address",
            ),
        ])
        return fh


class EmailForm(HelperMixin, forms.Form):
    email = forms.EmailField()
    confirm_email = forms.EmailField()
    password = forms.CharField(label="Please confirm your password", widget=forms.PasswordInput())

    def clean_confirm_email(self):
        email1 = self.cleaned_data.get("email")
        email2 = self.cleaned_data.get("confirm_email")
        if email1 and email2 and email1 != email2:
            raise ValidationError(
                "The two email fields did not match.",
                code="email_mismatch",
            )
        return email2

    @property
    def helper(self):
        fh = super().helper
        fh.layout.extend([
            Button.primary(
                name="submit",
                type="submit",
                value="Save and exit",
            ),
        ])
        return fh
