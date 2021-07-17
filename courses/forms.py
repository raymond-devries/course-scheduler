from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from courses import models


class SignUpForm(UserCreationForm):
    organization_name = forms.CharField(max_length=200)
    organization_city = forms.CharField(max_length=200)
    organization_state = forms.CharField(max_length=200)
    organization_zipcode = forms.CharField(max_length=20)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )


class CustomModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop("user")
        super().__init__(*args, **kwargs)


class PeriodForm(CustomModelForm):
    class Meta:
        model = models.Period
        exclude = ["organization"]

        widgets = {
            "start": forms.TimeInput(attrs={"type": "time"}),
            "end": forms.TimeInput(attrs={"type": "time"}),
        }


class TeacherForm(CustomModelForm):
    class Meta:
        model = models.Teacher
        exclude = ["organization"]


class BuildingForm(CustomModelForm):
    class Meta:
        model = models.Building
        exclude = ["organization"]


class RoomForm(CustomModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["building"].queryset = models.Building.objects.filter(
            organization__profile__user=self.current_user
        )

    class Meta:
        model = models.Room
        exclude = ["organization"]


class CourseForm(CustomModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["teacher"].queryset = models.Teacher.objects.filter(
            organization__profile__user=self.current_user
        )
        self.fields["room"].queryset = models.Room.objects.filter(
            organization__profile__user=self.current_user
        )
        self.fields["barred_period"].queryset = models.Period.objects.filter(
            organization__profile__user=self.current_user
        )

    class Meta:
        model = models.Course
        exclude = ["organization"]


class AnchoredCourseForm(CustomModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = models.Course.objects.filter(
            organization__profile__user=self.current_user
        )
        self.fields["period"].queryset = models.Period.objects.filter(
            organization__profile__user=self.current_user
        )
        self.fields["room"].queryset = models.Room.objects.filter(
            organization__profile__user=self.current_user
        )
        self.fields["teacher"].queryset = models.Teacher.objects.filter(
            organization__profile__user=self.current_user
        )

    class Meta:
        model = models.AnchoredCourse
        exclude = ["organization"]


class MandatoryScheduleForm(CustomModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["courses"].queryset = models.Course.objects.filter(
            organization__profile__user=self.current_user
        )

    def clean(self):
        if len(self.cleaned_data.get("courses")) > len(
            models.Period.objects.filter(organization__profile__user=self.current_user)
        ):
            raise ValidationError(
                "A mandatory schedule cannot have more classes than there is periods"
            )

    class Meta:
        model = models.MandatorySchedule
        exclude = ["organization"]


class SolvedScheduleForm(forms.ModelForm):
    class Meta:
        model = models.SolvedSchedule
        fields = ["name"]
        labels = {"name": "Schedule Name"}
        help_texts = {
            "name": "Provide a name for this created " "schedule for future reference"
        }
