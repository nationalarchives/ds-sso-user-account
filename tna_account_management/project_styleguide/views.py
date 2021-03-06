from django.shortcuts import render

from .forms import ExampleForm


def example_form(request):
    if request.method == "POST":
        form = ExampleForm(request.POST)
        form.add_error(None, "An example non-field error.")
    else:
        form = ExampleForm()

    return render(request, "patterns/pages/forms/example_form.html", {"form": form})
