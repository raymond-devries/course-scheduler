import dramatiq

from courses import solver


@dramatiq.actor
def task_solve(org_pk, solved_schedule_pk):
    solver.solve(org_pk, solved_schedule_pk)
