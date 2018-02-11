# Transcendence project

This project implements a social network. It will include user registration, 
user profiles, wall, private messages and API.

### Currently implemented:
At the moment, the basic project is deployed on Django 2.0 and configured:
 * added view to display information about the user
 * set up error logging in [Sentry](https://sentry.io/)
 * for configuration management used [django-configurations](https://github.com/jazzband/django-configurations)

# Installing
1. Install the required packages:
```
pip3 install -r requirements.txt
```
2. Set the value of the environment variable **SECRET_KEY** used in django 
settings.
3. Sign up on [Sentry](https://sentry.io/), create a new project in your account
 and get DSN (https://****@sentry.io/286271). Use this DSN in environment 
 variable **RAVEN_DSN**.
4. To run in development mode, use environment variable **DJANGO_CONFIGURATION**
 with the value **Dev**. To run on the server used the value **Prod** 
 (default value).

# Run and using
Create database and make migrations:
```
$ python3 manage.py makemigrations
$ python3 manage.py migrate
```
Run the application use the command:
```
$ python3 manage.py runserver 127.0.0.1:8000
```
The application will be available by link [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

Add user in db and get user id:
```
$ python3 manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.create_user(username='John', first_name='John', last_name='Lennon', email='lennon@thebeatles.com', password='johnpassword')
>>> user.id
1 
```
Information about the user is available by link 
[http://127.0.0.1:8000/users/1/](http://127.0.0.1:8000/users/1/), where *1* is user id.



# Project Goals

The code is written for educational purposes. Training course for web-developers - [DEVMAN.org](https://devman.org)
