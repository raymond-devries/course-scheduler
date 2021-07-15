from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    zipcode = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class OrgData(models.Model):
    organization = models.ForeignKey(Organization, models.CASCADE)

    class Meta:
        abstract = True


class Profile(OrgData):
    user = models.OneToOneField(User, models.CASCADE)


class Period(OrgData):
    number = models.PositiveIntegerField()
    start = models.TimeField()
    end = models.TimeField()
    avoid = models.BooleanField(default=False)

    def __str__(self):
        return f"Period {self.number}"


class Teacher(OrgData):
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Building(OrgData):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Room(OrgData):
    number = models.IntegerField()
    building = models.ForeignKey(Building, models.CASCADE)

    class Meta:
        unique_together = ("number", "building")

    def __str__(self):
        return f"{self.building}, Room {self.number}"


class Course(OrgData):
    name = models.CharField(max_length=150)
    number_offered = models.PositiveIntegerField(default=1)
    teacher = models.ManyToManyField(Teacher)
    room = models.ManyToManyField(Room)
    barred_period = models.ManyToManyField(Period, blank=True)

    def __str__(self):
        return self.name


class AnchoredCourse(OrgData):
    course = models.ForeignKey(Course, models.CASCADE)
    period = models.ForeignKey(Period, models.CASCADE)
    room = models.ForeignKey(Room, models.CASCADE)
    teacher = models.ForeignKey(Teacher, models.CASCADE)

    class Meta:
        unique_together = ("room", "period")

    def __str__(self):
        return (
            f"Course: {self.course}, Room: {self.room}, "
            f"Teacher: {self.teacher}, Period: {self.period}"
        )

    def clean(self):
        if self.period in self.course.barred_period.all():
            raise ValidationError(
                "The course cannot be anchored in a one of "
                "the course's barred periods"
            )
        if self.room not in self.course.room.all():
            raise ValidationError(
                "The course cannot be anchored in this room "
                "since the course does not have it as an option"
            )
        if self.teacher not in self.course.teacher.all():
            raise ValidationError(
                (
                    "The course cannot be anchored with this teacher "
                    "since the course does not have them as an option"
                )
            )

        if (
            AnchoredCourse.objects.filter(course=self.course).count()
            >= self.course.number_offered
        ):
            raise ValidationError(
                f"The number of anchored courses of this type "
                f"cannot exceed the number of times this course is offered"
            )


class MandatorySchedule(OrgData):
    name = models.CharField(max_length=100, blank=True)
    courses = models.ManyToManyField(Course)

    def __str__(self):
        return self.name
