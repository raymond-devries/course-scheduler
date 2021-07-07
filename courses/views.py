from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from courses import forms, models


def get_org(request):
    return request.user.profile.organization


def create_model_context(request, model, form, field_headers, fields, url_suffix):
    org = get_org(request)
    return {
        "instances": model.objects.filter(organization=org),
        "form": form(),
        "model_name": model.__name__,
        "field_headers": field_headers,
        "fields": fields,
        "url": {
            "add": "add_" + url_suffix,
            "edit": "edit_" + url_suffix,
            "delete": "delete_" + url_suffix,
        },
    }


def get_home_context(request):
    return {
        "period_data": create_model_context(
            request,
            models.Period,
            forms.PeriodForm,
            ["#", "Start", "End"],
            ["number", "start", "end"],
            "period",
        ),
        "teacher_data": create_model_context(
            request,
            models.Teacher,
            forms.TeacherForm,
            ["Last name", "First name"],
            ["last_name", "first_name"],
            "teacher",
        ),
        "building_data": create_model_context(
            request, models.Building, forms.BuildingForm, ["Name"], ["name"], "building"
        ),
        "room_data": create_model_context(
            request,
            models.Room,
            forms.RoomForm,
            ["Building", "#"],
            ["building", "number"],
            "room",
        ),
        "course_data": create_model_context(
            request,
            models.Course,
            forms.CourseForm,
            ["Name", "# Offered", "Teachers", "Rooms", "Barred Periods"],
            ["name", "number_offered", "teacher", "room", "barred_period"],
            "course",
        ),
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
            form.save_m2m()
            return partial_home(request, get_home_context(request))
    else:
        form = model_form()
    context = get_home_context(request)
    context[context_name]["form"] = form
    return partial_home(request, context)


@login_required
def edit_model(request, model, model_form, pk):
    instance = get_object_or_404(model, pk=pk, organization=get_org(request))
    if request.method == "POST":
        form = model_form(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return partial_home(request, context=get_home_context(request))
    else:
        form = model_form(instance=instance)
    context = {"edit_form": form, "model_name": model.__name__}
    return render(request, "courses/home_components/modal_edit.html", context=context)


@login_required
def delete_model(request, model, pk, message=""):
    instance = get_object_or_404(model, pk=pk, organization=get_org(request))
    if request.method == "DELETE":
        instance.delete()
        return partial_home(request, context=get_home_context(request))
    context = {"model_name": model.__name__, "message": message}
    return render(
        request,
        "courses/home_components/modal_delete_confirmation.html",
        context=context,
    )


def add_period(request):
    return add_model(request, forms.PeriodForm, "period_data")


def edit_period(request, pk):
    return edit_model(request, models.Period, forms.PeriodForm, pk)


def delete_period(request, pk):
    return delete_model(request, models.Period, pk)


def add_teacher(request):
    return add_model(request, forms.TeacherForm, "teacher_data")


def edit_teacher(request, pk):
    return edit_model(request, models.Teacher, forms.TeacherForm, pk)


def delete_teacher(request, pk):
    return delete_model(request, models.Teacher, pk)


def add_building(request):
    return add_model(request, forms.BuildingForm, "building_data")


def edit_building(request, pk):
    return edit_model(request, models.Building, forms.BuildingForm, pk)


def delete_building(request, pk):
    return delete_model(request, models.Building, pk)


def add_room(request):
    return add_model(request, forms.RoomForm, "room_data")


def edit_room(request, pk):
    return edit_model(request, models.Room, forms.RoomForm, pk)


def delete_room(request, pk):
    return delete_model(request, models.Room, pk)


def add_course(request):
    return add_model(request, forms.CourseForm, "course_data")


def edit_course(request, pk):
    return edit_model(request, models.Course, forms.CourseForm, pk)


def delete_course(request, pk):
    return delete_model(request, models.Course, pk)
