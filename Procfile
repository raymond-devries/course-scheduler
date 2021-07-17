release: python manage.py migrate
web: gunicorn scheduler.wsgi
worker: celery --app=scheduler.celery worker --loglevel=INFO