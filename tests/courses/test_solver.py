from model_bakery import baker
from pytest import mark

from courses import models, solver


# noinspection PyTypeChecker
@mark.django_db
def test_solve():
    org = baker.make(models.Organization)
    baker.make(models.Period, organization=org)
    assert solver.solve() is True
