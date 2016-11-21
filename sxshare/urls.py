# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

from django.conf.urls import include

from utils.urls import cbv_url_helper as url
import views

_urlpatterns = [
    url(r'^api/share/?$', views.ShareFileApi, translations=False),

    url(r'^(?P<token>[^/]+/[^/]+)/?$', views.SharedRelay),
    url(r'^(?P<token>[^/]+/[^/]+)/(?P<path>.+)$', views.SharedRelay),
]

urlpatterns = [
    url(r'^\.sxshare/', include(_urlpatterns))
]
