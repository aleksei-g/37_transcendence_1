import os
from fabric.api import cd, env, run, task, shell_env, put, with_settings,\
    hide, sudo
from fabric.contrib.files import exists
from fabtools import deb, require
from fabtools.python import virtualenv
from jinja2 import Environment, FileSystemLoader
from io import StringIO


env.project_path = (
    env.get('project_path') if env.get('project_path')
    else '/home/{}/{}/'.format(env.get('user'), env.get('project_name'))
)
env.virtualenv_path = (
    env.get('virtualenv_path') if env.get('virtualenv_path')
    else os.path.join(env.get('project_path'), 'venv/')
)
env.requirements_file = (
    env.get('requirements_file') if env.get('requirements_file')
    else os.path.join(env.get('project_path'), 'requirements.txt')
)
env.gunicorn_file_path = (
    env.get('gunicorn_file_path') if env.get('gunicorn_file_path')
    else '/etc/systemd/system/gunicorn.service'
)
env.socket_to_bind = (
    env.get('socket_to_bind') if env.get('socket_to_bind')
    else 'unix:{}myproject.sock'.format(env.get('project_path'))
)
env.listen_port = (
    env.get('listen_port') if env.get('listen_port')
    else 80
)
env.nginx_file_path = (
    env.get('nginx_file_path') if env.get('nginx_file_path')
    else '/etc/nginx/sites-available/{}'.format(env.get('project_name'))
)
env.static_path = (
    env.get('static_path') if env.get('static_path')
    else env.get('project_path')
)
env.system_packages = (
    env.get('system_packages') if env.get('system_packages')
    else 'python3 python3-pip python3-dev python3-venv python-dev libpq-dev '
         'postgresql postgresql-contrib nginx git'
)


def make_dir(path=None):
    if path and not exists(path):
        run('mkdir -p {}'.format(path))


@with_settings(
    hide('running', 'stdout', 'stderr', 'warnings'),
    cd('~postgres'),
    warn_only=True,
)
def user_exists(name):
    res = sudo(
        '''psql -t -A -c "SELECT COUNT(*) FROM pg_user
                    WHERE usename = '{}';"'''.format(name),
        user='postgres',
    )
    return '1' in res


@task
def debian_install(packages=env.get('system_packages')):
    deb.install(packages.split(' '), update=True)


@task
def setup_postgresql(db_user=env.get('db_user'),
                     db_password=env.get('db_password')):
    require.postgres.server()
    if not user_exists(db_user):
        require.postgres.create_user(
            db_user,
            password=db_password,
            createdb=True,
        )


@task
def create_db(db_name=env.get('db_name'), db_user=env.get('db_user')):
    make_dir('/var/lib/locales/supported.d/')
    require.postgres.database(db_name, owner=db_user)


@task
@with_settings(cd(env.project_path))
def get_latest_source(repo_url=env.get('repo_url')):
    if exists('.git'):
        run('git reset --hard HEAD')
        run('git pull origin master')
    else:
        run('git clone {} .'.format(repo_url))


@task
def create_virtualenv(virtualenv_path=env.virtualenv_path):
    if not exists(os.path.join(virtualenv_path, 'bin/pip')):
        run('python3 -m venv {}'.format(virtualenv_path))


@task
@with_settings(virtualenv(env.virtualenv_path))
def requirements_install(requirements_file=env.requirements_file):
    run('pip3 install -r {}'.format(requirements_file))


@task
@with_settings(
    cd(env.project_path),
    virtualenv(env.virtualenv_path),
    shell_env(
        DJANGO_SECRET_KEY=env.get('DJANGO_SECRET_KEY'),
        db_name=env.get('db_name'),
        db_user=env.get('db_user'),
        db_password=env.get('db_password'),
    ),
)
def update_database():
    run('python3 manage.py makemigrations')
    run('python3 manage.py migrate --noinput')


@task
@with_settings(
    cd(env.project_path),
    virtualenv(env.virtualenv_path),
    shell_env(
        DJANGO_SECRET_KEY=env.get('DJANGO_SECRET_KEY'),
        db_name=env.get('db_name'),
        db_user=env.get('db_user'),
        db_password=env.get('db_password'),
    ),
)
def create_superuser(
        username=env.get('DJANGO_SUPERUSER_NAME'),
        email=env.get('DJANGO_SUPERUSER_EMAIL'),
        password=env.get('DJANGO_SUPERUSER_PASSWORD'),
):
    if username and password:
        run('echo "from django.contrib.auth.models import User; '
            '\nif User.objects.filter(username=\'{0}\').count()==0:'
            '\n\tUser.objects.create_superuser(\'{0}\', \'{1}\', \'{2}\')" '
            '| python3 manage.py shell'.format(username, email, password))


@task
@with_settings(
    cd(env.project_path),
    virtualenv(env.virtualenv_path),
    shell_env(
        DJANGO_SECRET_KEY=env.get('DJANGO_SECRET_KEY'),
        db_name=env.get('db_name'),
        db_user=env.get('db_user'),
        db_password=env.get('db_password'),
    ),
)
def update_static_files():
    run('python3 manage.py collectstatic --noinput')


@task
def create_gunicorn_conf(gunicorn_file_path=env.gunicorn_file_path):
    template_loader = FileSystemLoader(searchpath='templates_conf')
    template_env = Environment(loader=template_loader)
    template = template_env.get_template('gunicorn.service')
    params_list = [
        'project_name',
        'project_path',
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
    make_dir(os.path.dirname(gunicorn_params['gunicorn_access_logfile_path']))
    make_dir(os.path.dirname(gunicorn_params['gunicorn_error_logfile_path']))
    put(
        StringIO(template.render(gunicorn_params)),
        gunicorn_file_path,
        use_sudo=True,
    )


@task
def create_nginx_conf(nginx_file_path=env.nginx_file_path):
    template_loader = FileSystemLoader(searchpath='templates_conf')
    template_env = Environment(loader=template_loader)
    template = template_env.get_template('nginx.conf')
    params_list = [
        'server_name',
        'listen_port',
        'static_path',
        'socket_to_bind',
        'nginx_access_logfile_path',
        'nginx_error_logfile_path',
        'nginx_loglevel',
    ]
    nginx_params = {param: env.get(param) for param in params_list}
    make_dir(os.path.dirname(nginx_params['nginx_access_logfile_path']))
    make_dir(os.path.dirname(nginx_params['nginx_error_logfile_path']))
    put(
        StringIO(template.render(nginx_params)),
        nginx_file_path,
        use_sudo=True,
    )
    if not exists(os.path.join(
            '/etc/nginx/sites-enabled',
            os.path.basename(nginx_file_path),
        ),
    ):
        sudo('ln -s {} /etc/nginx/sites-enabled'.format(nginx_file_path))


@task
def create_project_path(project_path=env.project_path):
    make_dir(project_path)


@task
def run_gunicorn():
    sudo('systemctl daemon-reload')
    sudo('systemctl restart gunicorn')
    sudo('systemctl enable gunicorn')


@task
def run_nginx():
    sudo('systemctl restart nginx')


@task
def bootstrap():
    debian_install()
    setup_postgresql()
    create_db()
    create_project_path()
    get_latest_source()
    create_virtualenv()
    requirements_install()
    update_database()
    create_superuser()
    update_static_files()
    create_gunicorn_conf()
    create_nginx_conf()
    run_gunicorn()
    run_nginx()
