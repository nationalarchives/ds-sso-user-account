from django.utils.translation import gettext_lazy as _
from tbxforms import forms as tbxforms_forms
from tbxforms.layout import Button, Size


class BaseForm(tbxforms_forms.BaseForm):
    """
    A base class that should be used/inherited by all forms.
    Outputs a standard form with the <form> tag.
    """

    @property
    def helper(self):
        fh = super().helper
        fh.html5_required = True
        fh.label_size = Size.MEDIUM
        fh.legend_size = Size.MEDIUM
        fh.form_error_title = _("There is a problem with your submission")
        return fh
