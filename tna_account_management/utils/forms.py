from django.utils.translation import gettext_lazy as _
from tbxforms import forms as tbxforms_forms
from tbxforms.layout import Button, Size
from wagtail.contrib.forms.forms import BaseForm as WagtailBaseForm


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


class BaseTaglessForm(BaseForm):
    """
    Outputs a form without the <form> tag.
    Useful when you want to have more control over the form within a template.
    """

    @property
    def helper(self):
        fh = super().helper
        fh.form_tag = False
        return fh


class BaseWagtailForm(BaseForm, WagtailBaseForm):
    """
    For forms built by `wagtail.contrib.forms` where we want to utilise our
    FormPage.action_text as the submit button text.
    """

    def __init__(self, *args, **kwargs):
        self.action_text = kwargs.pop("action_text", None)
        super().__init__(*args, **kwargs)

    @property
    def helper(self):
        fh = super().helper
        fh.layout.extend(
            [
                Button.primary(
                    name="submit",
                    type="submit",
                    value=self.action_text or _("Submit"),
                    css_class="form__submit",
                )
            ]
        )
        return fh


class WagtailFormBuilder(tbxforms_forms.BaseWagtailFormBuilder):
    """
    Instructs a Page model to use our `BaseWagtailForm` form variant, as well
    as inheriting some field/widget definitions from `BaseWagtailFormBuilder`.

    Usage: Add `form_builder = WagtailFormBuilder` to your form page model.
    """

    def get_form_class(self):
        return type("WagtailForm", (BaseWagtailForm,), self.formfields)
