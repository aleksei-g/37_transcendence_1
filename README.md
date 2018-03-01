# Transcendence project

This project implements a social network. It will include user registration, 
user profiles, wall, private messages and API.

The current version of the project is available by address [http://18.222.92.203](http://18.222.92.203).

### Currently implemented:
At the moment, the basic project is deployed on Django 2.0 and configured:
 * added view to display information about the user
 * set up error logging in [Sentry](https://sentry.io/)
 * for configuration management used [django-configurations](https://github.com/jazzband/django-configurations)
 * deployment of the project on the production server using fabric script

# Local installing
1. Create a directory and go to it. Clone project into this folder:
```
$ mkdir project_folder
$ cd project_folder
$ git clone https://github.com/aleksei-g/37_transcendence_1.git
```
2. Create a virtual environment with Python 3.5 and install all required 
packeges:
```
$ python3.5 -m venv virtualenv_path
$ source virtualenv_path/bin/activate
(virtualenv_path) $ pip install -r requirements.txt
```
3. Set the value of the environment variable **DJANGO_SECRET_KEY** used in django 
settings.
4. Sign up on [Sentry](https://sentry.io/), create a new project in your account
 and get DSN (https://****@sentry.io/286271). Use this DSN in environment 
 variable **RAVEN_DSN**.
5. To run in development mode, use environment variable **DJANGO_CONFIGURATION**
 with the value **Dev**. To run on the server used the value **Prod** 
 (default value).

# Run and using
Create database and make migrations:
```
(virtualenv_path) $ python3 manage.py makemigrations
(virtualenv_path) $ python3 manage.py migrate
```
Run the application use the command:
```
(virtualenv_path) $ python3 manage.py runserver 127.0.0.1:8000
```
The application will be available by link [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

Add user in db and get user id:
```
(virtualenv_path) $ python3 manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.create_user(username='John', first_name='John', last_name='Lennon', email='lennon@thebeatles.com', password='johnpassword')
>>> user.id
1 
```
Information about the user is available by link 
[http://127.0.0.1:8000/users/1/](http://127.0.0.1:8000/users/1/), where *1* is user id.

# Production deploy
For deploy in production server with Ubuntu server OS, use the fabric script 
that will take the following steps on the remote machine:
 * Install the required system packages. Python, Nginx, Postgresql and their requirements,
 * Configure the database: create a database and user,
 * Clone a project into the local folder from the remote repository,
 * Creates a virtual environment, installs all the packages from requirements.txt file,
 * run required django-command (migrate, collectstatic),
 * create superuser,
 * Configure and run Gunicorn,
 * Configure and run Nginx.

In project path create file **.server_conf** with project settings 
(see example in file **server_conf (example)**).

Required variables:
 * **user** - username on the remote host
 * **hosts** - IP address on the remote host (with SSH port)
 * **project_name** - project folder name
 * **repo_url** - link on remote repository project
 * **DJANGO_SECRET_KEY** - This is used to provide cryptographic signing, 
 and should be set to a unique, unpredictable value.
 * **DJANGO_ALLOWED_HOSTS** - host/domain names that this Django site can serve
 and specifies the virtual server nginx. To separate variables use '**,**'
  (192.168.1.1,www.site.com).
 * **db_name** - name database on Postgresql used for Django site
 * **db_user** - username to connect to the database on Postgresql
 * **db_password** - user password  to connect to the database on Postgresql.
 
In project path with active virtual environment use the following command 
to run deploying project on remote server:
```
(virtualenv_path) $ fab -c .server_conf bootstrap
```
After executing the command, the project will be available at the IP address 
remote host.

# Project Goals

The code is written for educational purposes. Training course for web-developers - [DEVMAN.org](https://devman.org)
