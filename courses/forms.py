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
