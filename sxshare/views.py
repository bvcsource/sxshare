# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

from __future__ import unicode_literals

import json
from mimetypes import guess_type
from urllib import quote

from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.utils.functional import cached_property
from django.views import generic
from ipware.ip import get_ip
from sxclient.exceptions import SXClusterNotFound, SXClientException

import core
import forms
from . import logger
from .api import sx
from utils import TimeoutError


class ShareFileApi(generic.edit.BaseFormView):
    """API for sharing files, compatible with SXWeb API."""
    form_class = forms.ShareFileForm

    def get(self, *args, **kwargs):
        return self.http_method_not_allowed(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ShareFileApi, self).get_form_kwargs()
        try:
            # Sxweb uses json format instead of form-encoded data
            kwargs['data'] = json.loads(self.request.body)
        except ValueError:
            pass
        return kwargs

    def post(self, *args, **kwargs):
        try:
            return super(ShareFileApi, self).post(*args, **kwargs)
        except TimeoutError as e:
            # Log details and fail with a generic message
            logger.error(e.message)
            return self.fail("Connection to SX cluster timed out.")

    def form_valid(self, form):
        data = form.cleaned_data
        token = core.share_file(data['path'],
                                expiration=data.get('expire_time'),
                                password=data.get('password'),
                                email=data.get('notify'))
        return self.succeed(token)

    def form_invalid(self, form):
        errors = self.format_errors(form.errors)
        return self.fail(errors)

    def fail(self, error):
        return JsonResponse({'status': False, 'error': error})

    def succeed(self, token):
        """
        Prepend `sxshare_address` from clusterMeta to the url, instead of
        hostname.
        """
        # Build url
        SXSHARE_PREFIX = '/.sxshare/'
        try:
            sxshare_address = sx.getClusterMetadata \
                .json_call()['clusterMeta']['sxshare_address'].decode('hex')
        except (KeyError, SXClientException):
            return self.fail(
                "Failed to build publink. " +
                "Please make sure you have `sxshare_address` " +
                "set in your cluster metadata.")
        url = reverse(SharedRelay.url_name, kwargs={'token': token})
        url = sxshare_address + url
        url = url.replace(SXSHARE_PREFIX, '', 1)  # Remove duplicate prefix
        if SXSHARE_PREFIX not in url:
            return self.fail(
                "Please make sure 'sxshare_address' ends with '{}'"
                .format(SXSHARE_PREFIX))

        return JsonResponse({'status': True, 'publink': url})

    def format_errors(self, error_dict):
        """Convert `form.errors` messages to a string."""
        parts = ["Failed to share file or directory."]
        for field_name, errors in error_dict.items():
            for error in errors:
                if error == "This field is required.":
                    error = "{} - {}".format(field_name, error)
                parts.append(error)
        return '\n'.join(parts)


class SharedRelay(generic.View):
    """Relay for shared file/dir views."""
    url_name = 'shared_file'
    template_name_missing = 'file_missing.html'

    def dispatch(self, *args, **kwargs):
        token = self.kwargs['token']
        file = core.get_shared_file_info(token)
        if file is None or file.is_expired or not file.exists():
            return render(self.request, self.template_name_missing)
        view = SharedDirView if file.is_dir else SharedFileView
        return view.as_view(file=file)(*args, **kwargs)


class FileBase(generic.FormView):
    """Mixin for shared file/dir views."""
    file = None  # Will be set through initkwargs
    form_class = forms.SharedFilePasswordForm

    def get_form_kwargs(self):
        kwargs = super(FileBase, self).get_form_kwargs()
        kwargs['authenticated'] = self.is_authenticated
        kwargs['check_password'] = self.file.check_password
        return kwargs

    def get_context_data(self, **kwargs):
        return super(FileBase, self).get_context_data(
            file=self.file, is_authenticated=self.is_authenticated, **kwargs)

    @cached_property
    def is_authenticated(self):
        if self.file.password:
            try:
                password = self.request.session['auth'][self.kwargs['token']]
                return self.file.check_password(password)
            except KeyError:
                return False
        return True

    def authenticate(self, form):
        if self.file.password:
            password = form.cleaned_data.get('password')
            auth = self.request.session.get('auth', {})
            auth[self.kwargs['token']] = password
            self.request.session['auth'] = auth


class SharedFileView(FileBase):
    template_name = 'file.html'

    def get(self, *args, **kwargs):
        if self.is_authenticated:
            # Maybe serve the file, maybe not
            headless = 'mozilla' not in self.request.META \
                .get('HTTP_USER_AGENT', '').lower()
            explicit_download = 'download' in self.request.GET
            if headless or explicit_download:
                return self.serve_file()
        return super(SharedFileView, self).get(*args, **kwargs)

    def form_valid(self, form):
        self.authenticate(form)
        return self.serve_file()

    def serve_file(self):
        client_ip = get_ip(self.request)
        return download_response(
            self.request, self.file, self.kwargs['token'], client_ip)


class PaginationMixin(object):
    """Mixin for applying pagination to a list of objects."""
    page_size = 20
    page_context = 9  # Show 9 pages in the paginator bar

    def get_pagination_source(self):
        raise NotImplementedError()

    def get_page(self, source):
        paginator = Paginator(source, self.page_size)
        try:
            num = int(self.request.GET.get('page'))
            # Clean `num`
            num = sorted([1, num, paginator.num_pages])[1]
        except (TypeError, ValueError):
            num = 1
        return paginator.page(num)

    def get_page_range(self, current_page):
        """Given a page object, return range of surrounding pages."""
        context = self.page_context
        num = current_page.number
        pivot = context / 2
        pages = current_page.paginator.page_range
        if len(pages) <= context:
            return pages
        elif num <= pivot:
            # First pages
            return pages[:context]
        elif num > len(pages) - pivot:
            # Last pages
            return pages[len(pages) - context:]
        else:
            # Somewhere in between
            return pages[num - pivot - 1:num + pivot]

    def get_context_data(self, **kwargs):
        source = self.get_pagination_source()
        page = self.get_page(source)
        page_range = self.get_page_range(page)
        return super(PaginationMixin, self).get_context_data(
            page=page, page_range=page_range, **kwargs)


class SharedDirView(PaginationMixin, FileBase):
    template_name = 'dir.html'

    def dispatch(self, *args, **kwargs):
        if self.path not in self.full_path:  # This is not a valid path
            return redirect(SharedRelay.url_name, token=self.kwargs['token'])
        return super(SharedDirView, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        if not core.is_dir(self.request.path):
            try:
                # Is it a file?
                client_ip = get_ip(self.request)
                return download_response(
                    self.request, self.file, self.kwargs['token'], client_ip,
                    self.path)
            except SXClusterNotFound:
                # No, it's a directory without a slash
                return redirect(self.request.path + '/')
            except KeyError as e:
                if e.message == 'blockSize':
                    # Bug in sxclient (downloading a directory)
                    return redirect(self.request.path + '/')
                raise
        return super(SharedDirView, self).get(*args, **kwargs)

    def form_valid(self, form):
        self.authenticate(form)
        return redirect(self.request.get_full_path())

    def get_pagination_source(self):
        return self.file.list_files(self.path)

    def get_context_data(self, **kwargs):
        return super(SharedDirView, self).get_context_data(
            is_subdir=bool(self.path), path=self.full_path, **kwargs)

    @property
    def path(self):
        path = self.kwargs.get('path', '')
        for c in '\\?*[]':
            path = path.replace(c, '\\' + c)
        return path

    @property
    def full_path(self):
        full_path = self.file.get_path(self.path)
        return full_path.decode('utf-8')


def download_response(request, file, token, ip=None, path=''):
    """Util for streaming a shared file."""
    if path:
        filename = core.get_filename(path)
    else:
        filename = file.filename
    if file.notify_email:
        core.create_download_marker(
            file, token, ip, path,
            user_agent=request.META.get('HTTP_USER_AGENT', ''))

    full_path = file.get_path(path)
    content_type = guess_type(full_path)[0]
    if content_type is None:
        content_type = 'application/octet-stream'

    response = StreamingHttpResponse(
        file.get_downloader(path),
        content_type=content_type)
    set_content_disposition_header(response, filename)
    return response


def set_content_disposition_header(response, filename):
    filename = quote(filename.encode('utf-8'))
    template = 'attachment; filename="{0}"; filename*=UTF-8\'\'{0};'
    response['Content-Disposition'] = template.format(filename)
