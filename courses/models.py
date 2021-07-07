from django.contrib.auth.models import User
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    zipcode = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, models.CASCADE)
    organization = models.ForeignKey(Organization, models.CASCADE)


class Period(models.Model):
    organization = models.ForeignKey(Organization, models.CASCADE)
    number = models.PositiveIntegerField()
    start = models.TimeField()
    end = models.TimeField()

    def __str__(self):
        return str(self.number)


class Teacher(models.Model):
    organization = models.ForeignKey(Organization, models.CASCADE)
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Building(models.Model):
    organization = models.ForeignKey(Organization, models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Room(models.Model):
    organization = models.ForeignKey(Organization, models.CASCADE)
    number = models.IntegerField()
    building = models.ForeignKey(Building, models.CASCADE)

    def __str__(self):
        return f"{self.building}, Room {self.number}"


class Course(models.Model):
    organization = models.ForeignKey(Organization, models.CASCADE)
    name = models.CharField(max_length=150)
    number_offered = models.PositiveIntegerField(default=1)
    teacher = models.ManyToManyField(Teacher)
    room = models.ManyToManyField(Room)
    barred_period = models.ManyToManyField(Period)


class AnchoredCourse(models.Model):
    organization = models.ForeignKey(Organization, models.CASCADE)
    course = models.ForeignKey(Course, models.CASCADE)
    room = models.ForeignKey(Room, models.CASCADE)
    period = models.ForeignKey(Period, models.CASCADE)

    def __str__(self):
        return f"Course: {self.course}, Room: {self.room}, Period: {self.period}"


class MandatorySchedule(models.Model):
    organization = models.ForeignKey(Organization, models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    courses = models.ManyToManyField(Course)

    def __str__(self):
        return self.name
