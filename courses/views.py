from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from courses import forms, models


def get_org(request):
    return request.user.profile.organization


def get_home_context(request):
    org = get_org(request)
    return {
        "periods": models.Period.objects.filter(organization=org),
        "period_form": forms.PeriodForm(),
        "teachers": models.Teacher.objects.filter(organization=org),
    }


@login_required
def home(request):
    context = get_home_context(request)
    return render(request, "courses/home.html", context=context)


def partial_home(request, context):
    return render(request, "courses/_home.html", context=context)


@login_required
def add_model(request, model_form, context_name):
    if request.method == "POST":
        form = model_form(request.POST)
        if form.is_valid():
            model_instance = form.save(commit=False)
            model_instance.organization = get_org(request)
            model_instance.save()
            return partial_home(request, get_home_context(request))
    else:
        form = model_form()
    context = get_home_context(request)
    context[context_name] = form
    return partial_home(request, context)


@login_required
def edit_model(request, model_form, pk):
    instance = get_object_or_404(models.Period, pk=pk, organization=get_org(request))
    if request.method == "POST":
        form = model_form(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return partial_home(request, context=get_home_context(request))
    else:
        form = model_form(instance=instance)
    context = {"edit_form": form}
    return render(request, "courses/modal_edit.html", context=context)


def add_period(request):
    return add_model(request, forms.PeriodForm, "period_form")


def edit_period(request, pk):
    return edit_model(request, forms.PeriodForm, pk)
