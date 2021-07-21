from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from courses import forms, models, solver, tasks


def signup(request):
    if request.method == "POST":
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.save()

            org_name = form.cleaned_data.get("organization_name")
            org_city = form.cleaned_data.get("organization_city")
            org_state = form.cleaned_data.get("organization_state")
            org_zipcode = form.cleaned_data.get("organization_zipcode")

            org = models.Organization.objects.create(
                name=org_name, city=org_city, state=org_state, zipcode=org_zipcode
            )
            models.Profile.objects.create(organization=org, user=user)

            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect("home")
    else:
        form = forms.SignUpForm()
    return render(request, "courses/accounts/signup.html", {"form": form})


def get_org(request):
    return request.user.profile.organization


def get_model_name(model):
    return model._meta.verbose_name.title()


def create_model_context(
    request, model, form, field_headers, fields, url_suffix, help_message=""
):
    org = get_org(request)
    return {
        "instances": model.objects.filter(organization=org),
        "form": form(user=request.user),
        "model_name": get_model_name(model),
        "field_headers": field_headers,
        "fields": fields,
        "url": {
            "add": "add_" + url_suffix,
            "edit": "edit_" + url_suffix,
            "delete": "delete_" + url_suffix,
        },
        "help_message": help_message,
    }


def get_home_context(request):
    return {
        "period_data": create_model_context(
            request,
            models.Period,
            forms.PeriodForm,
            ["#", "Start", "End", "Avoid"],
            ["number", "start", "end", "avoid"],
            "period",
            help_message="*If you mark a period to be avoided the schedule solver will "
            "try and minimize the amount of classes in that period",
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
        "anchored_course_data": create_model_context(
            request,
            models.AnchoredCourse,
            forms.AnchoredCourseForm,
            ["Course", "Room", "Period"],
            ["course", "room", "period"],
            "anchored_course",
        ),
        "mandatory_schedule_data": create_model_context(
            request,
            models.MandatorySchedule,
            forms.MandatoryScheduleForm,
            ["Name", "Courses"],
            ["name", "courses"],
            "mandatory_schedule",
        ),
    }


@login_required
def home(request):
    context = get_home_context(request)
    if request.method == "POST":
        form = forms.SolvedScheduleForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.organization = get_org(request)
            form.save()
            tasks.task_solve.send(get_org(request).pk, instance.pk)
            return redirect("solver_results")
    else:
        form = forms.SolvedScheduleForm()
    context["solved_schedule_form"] = form
    return render(request, "courses/home.html", context=context)


def partial_home(request, context):
    return render(request, "courses/_home.html", context=context)


@login_required
def add_model(request, model_form, context_name):
    if request.method == "POST":
        form = model_form(request.POST, user=request.user)
        if form.is_valid():
            model_instance = form.save(commit=False)
            model_instance.organization = get_org(request)
            model_instance.save()
            form.save_m2m()
            return partial_home(request, get_home_context(request))
    else:
        form = model_form(user=request.user)
    context = get_home_context(request)
    context[context_name]["form"] = form
    return partial_home(request, context)


@login_required
def edit_model(request, model, model_form, pk):
    instance = get_object_or_404(model, pk=pk, organization=get_org(request))
    if request.method == "POST":
        form = model_form(request.POST, instance=instance, user=request.user)
        context = get_home_context(request)
        if form.is_valid():
            form.save()
            context["include_modal"] = False
            return partial_home(request, context=context)
        context["include_modal"] = True
        context["edit_form"] = form
        context["model_name"] = get_model_name(model)
        return partial_home(request, context=context)
    else:
        form = model_form(instance=instance, user=request.user)
    context = {"edit_form": form, "model_name": get_model_name(model)}
    return render(request, "courses/home_components/modal_edit.html", context=context)


@login_required
def delete_model(request, model, pk, message=""):
    instance = get_object_or_404(model, pk=pk, organization=get_org(request))
    if request.method == "DELETE":
        instance.delete()
        return partial_home(request, context=get_home_context(request))
    context = {"model_name": get_model_name(model), "message": message}
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


def add_anchored_course(request):
    return add_model(request, forms.AnchoredCourseForm, "anchored_course_data")


def edit_anchored_course(request, pk):
    return edit_model(request, models.AnchoredCourse, forms.AnchoredCourseForm, pk)


def delete_anchored_course(request, pk):
    return delete_model(request, models.AnchoredCourse, pk)


def add_mandatory_schedule(request):
    return add_model(request, forms.MandatoryScheduleForm, "mandatory_schedule_data")


def edit_mandatory_schedule(request, pk):
    return edit_model(
        request, models.MandatorySchedule, forms.MandatoryScheduleForm, pk
    )


def delete_mandatory_schedule(request, pk):
    return delete_model(request, models.MandatorySchedule, pk)


@login_required
def solver_results(request, template):
    org = get_org(request)
    solved_schedules = models.SolvedSchedule.objects.filter(organization=org)
    return render(request, template, {"solved_schedules": solved_schedules})


def solver_results_full(request):
    return solver_results(request, "courses/solver_results.html")


def solver_results_table(request):
    return solver_results(request, "courses/solver_results_components/table.html")


@login_required
def solver_results_detail(request, pk):
    org = get_org(request)
    solved_schedule = get_object_or_404(models.SolvedSchedule, pk=pk, organization=org)
    schedule_items = models.ScheduleItem.objects.filter(solved_schedule=solved_schedule)
    rooms = (
        schedule_items.order_by("room_name")
        .values_list("room_name", flat=True)
        .distinct()
    )
    periods = (
        schedule_items.order_by("period_number")
        .values_list("period_number", flat=True)
        .distinct()
    )
    schedules = [
        [
            si.first()
            if (
                si := schedule_items.filter(room_name=room, period_number=period)
            ).exists()
            else (None, None)
            for room in rooms
        ]
        for period in periods
    ]
    schedules = zip(periods, schedules)
    context = {
        "solved_schedule": solved_schedule,
        "schedules": schedules,
        "rooms": rooms,
    }
    return render(request, "courses/sovler_result_detail.html", context=context)


@login_required
def delete_solved_schedule(request, pk):
    org = get_org(request)
    if request.method == "DELETE":
        solved_schedule = get_object_or_404(
            models.SolvedSchedule, organization=org, pk=pk
        )
        solved_schedule.delete()
    return solver_results_table(request)
