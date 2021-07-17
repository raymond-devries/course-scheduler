from celery import Celery

from scheduler import settings

app = Celery("scheduler")

app.config_from_object(settings)

app.autodiscover_tasks()
