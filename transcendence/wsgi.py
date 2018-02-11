import os


from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transcendence.settings")
os.environ.setdefault('DJANGO_CONFIGURATION', 'Prod')

application = get_wsgi_application()
