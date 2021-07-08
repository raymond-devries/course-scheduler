from django import forms

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
    class Meta:
        model = models.MandatorySchedule
        exclude = ["organization"]
