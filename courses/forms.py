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


class PeriodForm(forms.ModelForm):
    class Meta:
        model = models.Period
        exclude = ["organization"]

        widgets = {
            "start": forms.TimeInput(attrs={"type": "time"}),
            "end": forms.TimeInput(attrs={"type": "time"}),
        }


class TeacherForm(forms.ModelForm):
    class Meta:
        model = models.Teacher
        exclude = ["organization"]


class BuildingForm(forms.ModelForm):
    class Meta:
        model = models.Building
        exclude = ["organization"]


class RoomForm(forms.ModelForm):
    class Meta:
        model = models.Room
        exclude = ["organization"]


class CourseForm(forms.ModelForm):
    class Meta:
        model = models.Course
        exclude = ["organization"]


class AnchoredCourseForm(forms.ModelForm):
    class Meta:
        model = models.AnchoredCourse
        exclude = ["organization"]


class MandatoryScheduleForm(forms.ModelForm):
    def clean(self):
        if len(c := self.cleaned_data.get("courses")) > len(
            models.Period.objects.filter(organization=c.first().organization)
        ):
            raise ValidationError(
                "A mandatory schedule cannot have more classes than there is periods"
            )

    class Meta:
        model = models.MandatorySchedule
        exclude = ["organization"]
