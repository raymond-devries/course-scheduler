import pyomo.environ as pe
import pyomo.opt as po

from courses import models


# noinspection PyUnusedLocal
def get_possible_assignments(
    m: pe.ConcreteModel,
    period: models.Period,
    teacher: models.Teacher,
    room: models.Room,
    course: models.Course,
):
    period = models.Period.objects.get(pk=period)
    teacher = models.Teacher.objects.get(pk=teacher)
    room = models.Room.objects.get(pk=room)
    course = models.Course.objects.get(pk=course)
    if (
        period not in course.barred_period.all()
        and teacher in course.teacher.all()
        and room in course.room.all()
    ):
        return True
    return False


# noinspection PyUnusedLocal
def get_anchored_courses(
    m: pe.ConcreteModel,
    period: models.Period,
    teacher: models.Teacher,
    room: models.Room,
    course: models.Course,
):
    period = models.Period.objects.get(pk=period)
    teacher = models.Teacher.objects.get(pk=teacher)
    room = models.Room.objects.get(pk=room)
    course = models.Course.objects.get(pk=course)
    return models.AnchoredCourse.objects.filter(
        period=period, room=room, course=course, teacher=teacher
    ).exists()


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
    pyomo_model.anchored = pe.Param(
        pyomo_model.periods,
        pyomo_model.teachers,
        pyomo_model.rooms,
        pyomo_model.courses,
        initialize=get_anchored_courses,
    )
    pyomo_model.possible_assignment = pe.Param(
        pyomo_model.periods,
        pyomo_model.teachers,
        pyomo_model.rooms,
        pyomo_model.courses,
        initialize=get_possible_assignments,
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

    return pyomo_model


def solve(org: models.Organization):
    pyomo_model = create_model(org)
    solver = po.SolverFactory("glpk")
    solver_results = solver.solve(pyomo_model, tee=True)

    if (solver_results.solver.status == po.SolverStatus.ok) and (
        solver_results.solver.termination_condition == po.TerminationCondition.optimal
    ):
        results = {}
        for p in pyomo_model.periods:
            for t in pyomo_model.teachers:
                for r in pyomo_model.rooms:
                    for c in pyomo_model.courses:
                        key = (
                            models.Period.objects.get(pk=p),
                            models.Room.objects.get(pk=r),
                        )
                        if pe.value(pyomo_model.assignments[p, t, r, c]):
                            if key in results:
                                raise ValueError("Double assignment")
                            results[key] = (
                                models.Course.objects.get(pk=c),
                                models.Teacher.objects.get(pk=t),
                            )
    else:
        results = False

    return results
