from fabric.api import env, settings, hide, sudo
import os


def set_env():
    env.project_path = (
        env.get('project_path') if env.get('project_path')
        else '/home/{}/web/{}/'.format(
            env.get('user'),
            env.get('project_name'),
        )
    )
    env.src_path = os.path.join(env.get('project_path'), 'src/')
    env.virtualenv_path = os.path.join(env.get('project_path'), '.venv/')
    env.system_packages = 'python3 python3-pip python3-dev python3-venv ' \
        'python-dev libpq-dev postgresql postgresql-contrib nginx git'
    env.gunicorn_file_path = '/etc/systemd/system/gunicorn.service'
    env.socket_to_bind = 'unix:{}myproject.sock'\
        .format(env.get('project_path'))
    env.number_of_workers = 3
    env.gunicorn_access_logfile_path = os.path.join(
        env.get('project_path'),
        'log/gunicorn/access_log',
    )
    env.gunicorn_error_logfile_path = os.path.join(
        env.get('project_path'),
        'log/gunicorn/error_log',
    )
    env.gunicorn_loglevel = 'error'
    env.nginx_file_path = '/etc/nginx/sites-available/{}'\
        .format(env.get('project_name'))
    env.listen_port = 80
    env.static_path = env.get('src_path')
    env.nginx_access_logfile_path = os.path.join(
        env.get('project_path'),
        'log/nginx/access_log',
    )
    env.nginx_error_logfile_path = os.path.join(
        env.get('project_path'),
        'log/nginx/error_log',
    )
    env.nginx_loglevel = 'error'
    env.key_filename = '~/.ssh/id_rsa'


def user_exists(username):
    with settings(
            hide('running', 'stdout', 'stderr', 'warnings'),
            warn_only=True,
    ):
        res = sudo(
            '''psql -t -A -c "SELECT COUNT(*) FROM pg_user
                        WHERE usename = '{}';"'''.format(username),
            user='postgres',
        )
    return '1' in res
