# Class Scheduler

Required Environment Variables:

* `DJANGO_SECRET_KEY`: Required django secret key
* `DEBUG`: Defaults to False, only set to True if you are developing locally
* `ALLOWED_HOSTS`: Sets allowed hosts as a comma separated list.
  e.g. `127.0.0.1,0.0.0.0`
* `NEOS_EMAIL`: Email associated with the neos solver
* `DATABASE_URL`: Url for the database in accordance with the url scheme
  of [dj-database-url](https://github.com/jacobian/dj-database-url#url-schema)