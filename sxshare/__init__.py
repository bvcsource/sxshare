# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

import logging
import subprocess

logger = logging.getLogger('sxshare')

VERSION = (1, 0, 3, 'dev')


def get_version():
    version = '.'.join(str(n) for n in VERSION)
    git_hash = get_git_hash()
    if git_hash is not None:
        version = '{} (@{})'.format(version, git_hash)
    return version


def get_git_hash():
    try:
        return subprocess.check_output([
            'git', 'rev-parse', '--short', 'HEAD',
        ]).strip()
    except subprocess.CalledProcessError:
        return None
