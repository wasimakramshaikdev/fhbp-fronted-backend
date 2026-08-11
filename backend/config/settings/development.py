import os
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# If Redis is not explicitly configured, execute Celery tasks synchronously (in-process)
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_ALWAYS_EAGER', 'True' if not os.getenv('CELERY_BROKER_URL') or '127.0.0.1' in os.getenv('CELERY_BROKER_URL') else 'False') == 'True'
CELERY_TASK_EAGER_PROPAGATES = True
