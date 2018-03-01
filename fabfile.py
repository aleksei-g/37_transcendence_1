import os
from fabric.api import cd, env, run, task, shell_env, put, sudo
from fabric.contrib.files import exists
from fabtools import deb, require
from fabtools.python import virtualenv
from jinja2 import Environment, FileSystemLoader
from io import StringIO
from fabric_helpers import set_env, user_exists


def make_dir(path=None, use_sudo=False):
    if path and not exists(path):
        if use_sudo:
            sudo('mkdir -p {}'.format(path))
        else:
            run('mkdir -p {}'.format(path))


def install_system_packages():
    deb.install(env.system_packages.split(' '), update=True)


def make_all_required_dir():
    make_dir(env.project_path)
    make_dir(env.src_path)
    make_dir(os.path.dirname(env.gunicorn_access_logfile_path))
    make_dir(os.path.dirname(env.gunicorn_error_logfile_path))
    make_dir(os.path.dirname(env.nginx_access_logfile_path))
    make_dir(os.path.dirname(env.nginx_error_logfile_path))
    make_dir('/var/lib/locales/supported.d/', True)


def setup_postgresql():
    require.postgres.server()
    if not user_exists(env.get('db_user')):
        require.postgres.create_user(
            env.get('db_user'),
            password=env.get('db_password'),
            createdb=True,
            )


def create_db():
    require.postgres.database(env.get('db_name'), owner=env.get('db_user'))


def get_latest_source():
    if exists('.git'):
        run('git reset --hard HEAD')
        run('git pull origin master')
    else:
        run('git clone {} .'.format(env.get('repo_url')))


def create_virtualenv():
    if not exists(os.path.join(env.virtualenv_path, 'bin/pip')):
        run('python3 -m venv {}'.format(env.virtualenv_path))


def install_requirements():
    requirements_file = os.path.join(
        env.get('src_path'),
        'requirements.txt',
    )
    run('pip3 install -r {}'.format(requirements_file))


def update_database():
    run('python3 manage.py makemigrations')
    run('python3 manage.py migrate --noinput')


def create_superuser():
    if env.get('DJANGO_SUPERUSER_NAME') and \
            env.get('DJANGO_SUPERUSER_PASSWORD'):
        run('echo "from django.contrib.auth.models import User; '
            '\nif User.objects.filter(username=\'{0}\').count()==0:'
            '\n\tUser.objects.create_superuser(\'{0}\', \'{1}\', \'{2}\')" '
            '| python3 manage.py shell'
            .format(
                env.get('DJANGO_SUPERUSER_NAME'),
                env.get('DJANGO_SUPERUSER_EMAIL'),
                env.get('DJANGO_SUPERUSER_PASSWORD'),
                )
            )


def update_static_files():
    run('python3 manage.py collectstatic --noinput')


def create_gunicorn_conf():
    template_loader = FileSystemLoader(searchpath='templates_conf')
    template_env = Environment(loader=template_loader)
    template = template_env.get_template('gunicorn.service')
    params_list = [
        'project_name',
        'src_path',
        'virtualenv_path',
        'user',
        'DJANGO_SECRET_KEY',
        'DJANGO_ALLOWED_HOSTS',
        'RAVEN_DSN',
        'socket_to_bind',
        'number_of_workers',
        'gunicorn_access_logfile_path',
        'gunicorn_error_logfile_path',
        'gunicorn_loglevel',
        'db_user',
        'db_password',
        'db_name',
    ]
    gunicorn_params = {param: env.get(param) for param in params_list}
    put(
        StringIO(template.render(gunicorn_params)),
        env.gunicorn_file_path,
        use_sudo=True,
    )


def create_nginx_conf():
    template_loader = FileSystemLoader(searchpath='templates_conf')
    template_env = Environment(loader=template_loader)
    template = template_env.get_template('nginx.conf')
    params_list = [
        'DJANGO_ALLOWED_HOSTS',
        'listen_port',
        'static_path',
        'socket_to_bind',
        'nginx_access_logfile_path',
        'nginx_error_logfile_path',
        'nginx_loglevel',
    ]
    nginx_params = {param: env.get(param) for param in params_list}
    put(
        StringIO(template.render(nginx_params)),
        env.nginx_file_path,
        use_sudo=True,
    )
    if not exists(os.path.join(
            '/etc/nginx/sites-enabled',
            os.path.basename(env.nginx_file_path),
        ),
    ):
        sudo('ln -s {} /etc/nginx/sites-enabled'.format(env.nginx_file_path))
    sudo('rm -f /etc/nginx/sites-enabled/default')


@task
def restart_gunicorn():
    sudo('systemctl daemon-reload')
    sudo('systemctl restart gunicorn')


def enable_gunicorn():
    sudo('systemctl enable gunicorn')


@task
def restart_nginx():
    sudo('systemctl restart nginx')


@task
def bootstrap():
    set_env()
    install_system_packages()
    make_all_required_dir()
    setup_postgresql()
    create_db()
    create_virtualenv()
    with cd(env.src_path):
        get_latest_source()
        with virtualenv(env.virtualenv_path):
            install_requirements()
            with shell_env(
                DJANGO_SECRET_KEY=env.get('DJANGO_SECRET_KEY'),
                db_name=env.get('db_name'),
                db_user=env.get('db_user'),
                db_password=env.get('db_password'),
            ):
                update_database()
                create_superuser()
                update_static_files()
    create_gunicorn_conf()
    create_nginx_conf()
    restart_gunicorn()
    enable_gunicorn()
    restart_nginx()
