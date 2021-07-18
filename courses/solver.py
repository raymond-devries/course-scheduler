import itertools
import logging

import dramatiq
import pyomo.environ as pe
import pyomo.opt as po
from celery import shared_task
from pyomo.gdp import Disjunction

from courses import models


def get_unique_combos(iterable1, iterable2):
    permut = itertools.permutations(iterable1, len(iterable2))
    return [list(zip(comb, iterable2)) for comb in permut]


def get_possible_assignments(course_pks):
    data = {}
    for pk in course_pks:
        course = models.Course.objects.get(pk=pk)
        data[pk] = {
            "barred_periods": set(course.barred_period.values_list("pk", flat=True)),
            "teachers": set(course.teacher.values_list("pk", flat=True)),
            "rooms": set(course.room.values_list("pk", flat=True)),
        }

    return data


# noinspection PyUnusedLocal
def get_number_of_courses_offered(m: pe.ConcreteModel, course: models.Course):
    course = models.Course.objects.get(pk=course)
    return course.number_offered


def create_model(org: models.Organization):
    pyomo_model = pe.ConcreteModel()

    pyomo_model.periods = pe.Set(
        initialize=models.Period.objects.filter(organization=org).values_list(
            "pk", flat=True
        )
    )
    pyomo_model.teachers = pe.Set(
        initialize=models.Teacher.objects.filter(organization=org).values_list(
            "pk", flat=True
        )
    )
    pyomo_model.rooms = pe.Set(
        initialize=models.Room.objects.filter(organization=org).values_list(
            "pk", flat=True
        )
    )
    pyomo_model.courses = pe.Set(
        initialize=models.Course.objects.filter(organization=org).values_list(
            "pk", flat=True
        )
    )
    pyomo_model.avoided_periods = pe.Set(
        initialize=models.Period.objects.filter(
            organization=org, avoid=True
        ).values_list("pk", flat=True)
    )
    mandatory_schedules = [
        list(mc.courses.all().values_list("pk", flat=True))
        for mc in models.MandatorySchedule.objects.filter(organization=org)
    ]

    mandatory_possible_combos = [
        get_unique_combos(pyomo_model.periods, schedule)
        for schedule in mandatory_schedules
    ]

    anchored_courses = set(
        models.AnchoredCourse.objects.filter(organization=org).values_list(
            "period", "teacher", "room", "course"
        )
    )

    pyomo_model.anchored = pe.Param(
        pyomo_model.periods,
        pyomo_model.teachers,
        pyomo_model.rooms,
        pyomo_model.courses,
        initialize=lambda m, p, t, r, c: (p, t, r, c) in anchored_courses,
    )

    possibilities = get_possible_assignments(pyomo_model.courses)

    pyomo_model.possible_assignment = pe.Param(
        pyomo_model.periods,
        pyomo_model.teachers,
        pyomo_model.rooms,
        pyomo_model.courses,
        initialize=lambda m, p, t, r, c: p not in possibilities[c]["barred_periods"]
        and t in possibilities[c]["teachers"]
        and r in possibilities[c]["rooms"],
    )
    pyomo_model.course_number_offered = pe.Param(
        pyomo_model.courses, initialize=get_number_of_courses_offered
    )
    pyomo_model.assignments = pe.Var(
        pyomo_model.periods,
        pyomo_model.teachers,
        pyomo_model.rooms,
        pyomo_model.courses,
        within=pe.Binary,
    )

    pyomo_model.cons = pe.ConstraintList()

    pyomo_model.opt = pe.Objective(
        expr=sum(
            pyomo_model.assignments[ap, t, r, c]
            for ap in pyomo_model.avoided_periods
            for t in pyomo_model.teachers
            for r in pyomo_model.rooms
            for c in pyomo_model.courses
        )
    )

    for p in pyomo_model.periods:
        for t in pyomo_model.teachers:
            for r in pyomo_model.rooms:
                for c in pyomo_model.courses:
                    pyomo_model.cons.add(
                        pyomo_model.assignments[p, t, r, c]
                        <= pyomo_model.possible_assignment[p, t, r, c]
                    )
                    pyomo_model.cons.add(
                        pyomo_model.assignments[p, t, r, c]
                        >= pyomo_model.anchored[p, t, r, c]
                    )

    for p in pyomo_model.periods:
        for t in pyomo_model.teachers:
            pyomo_model.cons.add(
                sum(
                    pyomo_model.assignments[p, t, r, c]
                    for r in pyomo_model.rooms
                    for c in pyomo_model.courses
                )
                <= 1
            )

    for p in pyomo_model.periods:
        for r in pyomo_model.rooms:
            pyomo_model.cons.add(
                sum(
                    pyomo_model.assignments[p, t, r, c]
                    for t in pyomo_model.teachers
                    for c in pyomo_model.courses
                )
                <= 1
            )

    for c in pyomo_model.courses:
        pyomo_model.cons.add(
            sum(
                pyomo_model.assignments[p, t, r, c]
                for p in pyomo_model.periods
                for t in pyomo_model.teachers
                for r in pyomo_model.rooms
            )
            == pyomo_model.course_number_offered[c]
        )

    for i, combos in enumerate(mandatory_possible_combos):
        setattr(
            pyomo_model,
            f"disjunction{i}",
            Disjunction(
                expr=[
                    [
                        sum(
                            pyomo_model.assignments[p, t, r, c]
                            for t in pyomo_model.teachers
                            for r in pyomo_model.rooms
                        )
                        >= 1
                        for p, c in combo
                    ]
                    for combo in combos
                ]
            ),
        )

    return pyomo_model


def get_schedule_item(org, solved_schedule, p, t, r, c):
    period = models.Period.objects.get(pk=p)
    teacher = models.Teacher.objects.get(pk=t)
    room = models.Room.objects.get(pk=r)
    course = models.Course.objects.get(pk=c)

    return models.ScheduleItem(
        organization=org,
        solved_schedule=solved_schedule,
        period_pk=period.pk,
        period_number=period.number,
        period_start=period.start,
        period_end=period.end,
        room_pk=room.pk,
        room_name=str(room),
        teacher_name=str(teacher),
        course_name=course.name,
    )


def solve(org_pk: int, solved_schedule_pk: int):
    org = models.Organization.objects.get(pk=org_pk)
    solved_schedule = models.SolvedSchedule.objects.get(pk=solved_schedule_pk)
    models.ScheduleItem.objects.filter(solved_schedule=solved_schedule).delete()
    try:
        pyomo_model = create_model(org)
        solver = po.SolverManagerFactory("neos")
        solver_results = solver.solve(pyomo_model, tee=True, opt="ipopt")
    except ValueError as e:
        logging.error(f"Solved schedule {solved_schedule_pk} failed. ERROR: {e}")
        solved_schedule.finished = True
        solved_schedule.save()
        return solved_schedule.pk

    if (solver_results.solver.status == po.SolverStatus.ok) and (
        solver_results.solver.termination_condition == po.TerminationCondition.optimal
    ):

        schedule_items = [
            get_schedule_item(org, solved_schedule, p, t, r, c)
            for p in pyomo_model.periods
            for t in pyomo_model.teachers
            for r in pyomo_model.rooms
            for c in pyomo_model.courses
            if pe.value(pyomo_model.assignments[p, t, r, c])
        ]
        models.ScheduleItem.objects.bulk_create(schedule_items)
        solved_schedule.solved = True

    solved_schedule.finished = True
    solved_schedule.save()
    return solved_schedule.pk
