# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

from sxshare import get_version


def sx_share(request):
    context = {
        'VERSION': get_version(),
    }
    return context
