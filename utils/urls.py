# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

from functools import wraps

from django.utils.translation import deactivate
from django.conf.urls import url
from django.contrib.auth.decorators import login_required


def cbv_url_helper(regex, cbv, kwargs=None, name=None, prefix='', login=False,
                   translations=True):
    """Return an url instance from given regex and class-based view.

    You'd probably want to use import..as statement for loading this function:
    from utils.urls import cbv_url_helper as url
    Then go from this:
    url('^profile$',
        login_required(v.ProfileView.as_view()),
        name='profile')
    To this:
    url('^profile$', v.ProfileView)

    Like the standard url function, it can include() other urlconfs.

    It may not seem much, but as your urls.py file grows bigger and bigger,
    every squished line counts.
    """
    if isinstance(cbv, tuple):
        # Assuming it's a result of an `include` call.
        return url(regex, cbv)

    if not name:
        name = getattr(cbv, 'url_name', None)

    view = cbv.as_view()
    if not translations:
        view = disable_translations(view)
    if login:
        view = login_required(view)

    return url(regex, view, kwargs=kwargs, name=name, prefix=prefix)


def disable_translations(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        deactivate()
        return view(*args, **kwargs)
    return wrapped
