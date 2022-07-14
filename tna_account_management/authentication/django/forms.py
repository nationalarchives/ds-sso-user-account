from django.contrib.auth.forms import AuthenticationForm
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
