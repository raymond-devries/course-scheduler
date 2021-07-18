release: python manage.py migrate
release: python manage.py migrate django_dramatiq
web: gunicorn scheduler.wsgi
worker: python manage.py rundramatiq --processes 1 --threads 1