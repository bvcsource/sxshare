# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

"""
* * *

WSGI config for sxshare project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sxshare.settings")

application = get_wsgi_application()
