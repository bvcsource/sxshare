# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

from __future__ import absolute_import

from django.template import Library
from django.utils.html import format_html


register = Library()


@register.filter(name='icon')
def icon(file, args=''):
    classes = ['ir'] + args.split()
    if file.is_dir:
        classes.append('icon-folder')
    else:
        classes.append('icon-blank')
    return format_html('<span class="{}"></span>', ' '.join(classes))
