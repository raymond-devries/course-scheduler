from django import forms
from django.core.exceptions import ValidationError

from courses import models


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
