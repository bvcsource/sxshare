# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

from __future__ import unicode_literals

from django.conf import settings
from django.core.checks import Critical, register

from sxclient import Cluster, UserData, SXController, SXFileCat, SXFileUploader
from sxclient.exceptions import SXClientException

from . import logger


conf = settings.SX_CONF


def _get_user_data():
    if 'admin_key' in conf:
        return UserData.from_key(conf['admin_key'])
    elif 'admin_key_path' in conf:
        return UserData.from_key_path(conf['admin_key_path'])
    else:
        raise ValueError(
            "You must provide either 'admin_key' or 'admin_key_path' "
            "in the sx config.")


def _get_cluster():
    ip_addresses = conf.get('ip_addresses')
    if isinstance(ip_addresses, basestring):
        ip_addresses = [ip_addresses]
    kwargs = {
        'name': conf.get('cluster'),
        'ip_addresses': ip_addresses,
        'is_secure': conf.get('is_secure', True),
        'port': conf.get('port'),
        'verify_ssl_cert':
        conf.get('certificate') or conf.get('verify_ca')
    }
    return Cluster(**kwargs)

cluster = _get_cluster()
user_data = _get_user_data()
sx = SXController(cluster, user_data)

downloader = SXFileCat(sx)
uploader = SXFileUploader(sx)


@register()
def sx_check(app_configs, **kwargs):
    """Smoketest the connection with SX cluster."""
    errors = []
    try:
        sx.listUsers.call()
    except SXClientException as e:
        logger.critical(
            "Couldn't initialize sx console. Error message: " + e.message)
        hint = "Check if your sx user has admin priveleges." \
            if '403' in e.message else None
        errors.append(Critical("SXClient error ocurred: {}".format(e),
                               hint=hint))
    return errors
