# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

from __future__ import unicode_literals

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

from django.utils.translation import ugettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import yaml


def _check_permissions(path):
    if not os.path.isfile(path):
        return
    permissions = os.stat(path).st_mode
    assert oct(permissions)[-2:] == '00', (
        "Please make sure that this file is not "
        "accessible to other users: {}".format(path))

# Path to SX Share config file
_conf_path = os.path.join(BASE_DIR, 'conf.yaml')
_check_permissions(_conf_path)
with open(_conf_path) as f:
    _conf = yaml.safe_load(f)
    SERVER_CONF = _conf.get('server') or {}
    APP_CONF = _conf.get('app') or {}
    SX_CONF = _conf.get('sx') or {}
    EMAIL_CONF = _conf.get('mailing') or {}


def _as_list(value):
    """Ensure that the value is a list."""
    if not isinstance(value, list):
        value = [value]
    return value


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '@6ddlfl7y=rkus3%hs*p(9-uvxmxvkpka0-zr@m#1tx(kzx@z+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = SERVER_CONF.get('debug', False)

if not DEBUG:
    ALLOWED_HOSTS = _as_list(SERVER_CONF['hosts'])


# Application definition

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions',
    'sizefield',

    'sxshare',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'sxshare.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'sxshare.context_processors.sx_share',
            ],
        },
    },
]

from django.template.base import add_to_builtins
add_to_builtins('django.templatetags.i18n')

WSGI_APPLICATION = 'sxshare.wsgi.application'


# Server info
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
APPEND_SLASH = False


# Sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'


# Mailing
EMAIL_HOST = EMAIL_CONF.get('host')
EMAIL_PORT = EMAIL_CONF.get('port')
EMAIL_HOST_USER = EMAIL_CONF.get('user')
EMAIL_HOST_PASSWORD = EMAIL_CONF.get('password')
EMAIL_USE_SSL = EMAIL_CONF.get('ssl')
EMAIL_USE_TLS = EMAIL_CONF.get('tls')
DEFAULT_FROM_EMAIL = EMAIL_CONF.get('from')

# Notification options
NOTIFICATION_CONF = EMAIL_CONF.get('notifications') or {}
NOTIFICATION_SUBJECT = NOTIFICATION_CONF.get('email_subject')
NOTIFICATION_HEAD_FILE = NOTIFICATION_CONF.get('email_head_file')
NOTIFICATION_TAIL_FILE = NOTIFICATION_CONF.get('email_tail_file')


# Admin e-mails
SERVER_EMAIL = DEFAULT_FROM_EMAIL
ADMINS = APP_CONF.get('report_to')
if ADMINS:
    assert SERVER_EMAIL, "The 'mailing.from' field is required " \
        "if 'app.report_to' is given."
    ADMINS = [('Admin', email) for email in _as_list(ADMINS)]


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', _("English")),
    ('de', _("German")),
    ('it', _("Italian")),
    ('pl', _("Polish")),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, '../sx-translations/sxshare'),
)


TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/.sxshare/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/srv/logs/django.log',
            'formatter': 'file',
        },
    },
    'loggers': {
        'django': {
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'sxshare': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
    'formatters': {
        'file': {
            'format': '\n%(levelname)s %(asctime)s\n%(message)s'
        },
    }
}
if DEBUG:
    LOGGING['handlers']['file']['filename'] = 'django.log'
    LOGGING['loggers']['django']['handlers'] = ['console']
else:
    LOGGING['loggers']['django']['handlers'] = ['mail_admins', 'file']
