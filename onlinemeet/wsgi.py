"""
WSGI config for onlinemeet project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onlinemeet.settings')

application = get_wsgi_application()


