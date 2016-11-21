# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

import json
import os
from datetime import datetime
from io import BytesIO
from itertools import chain
from time import time

from django.contrib.auth.hashers import make_password, check_password
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from sxclient import SXFileDownloader
from sxclient.exceptions import SXClusterNotFound

from utils import timeout
from sxshare.api import sx, downloader, uploader


share_links_volname = '__sharelinks__'
notify_dir = 'notify'


if share_links_volname not in sx.listVolumes.json_call()['volumeList']:
    replica = len(sx.listNodes.json_call()['nodeList'])
    sx.createVolume.call(
        share_links_volname,
        volumeSize=1024 * 1024 * 1024,  # 1gb
        owner='admin',
        replicaCount=replica,
        maxRevisions=1)


def is_dir(path):
    return path.endswith('/')


def split_path(path):
    """Return volume name and file path for given full path."""
    volname, path = path.lstrip('/').split('/', 1)
    if not path:
        path = '/'
    return volname, path


def get_filename(path):
    dir = is_dir(path)
    filename = path.strip('/').split('/')[-1]
    if dir:
        filename += '/'
    return filename


def share_file(path, expiration=None, password=None, email=None):
    """Create a info file, which stores information about the shared file.

    Returns token for the shared file url.
    Raises utils.timeout.TimeoutError if upload took too long
    """
    # Prepare the data
    filename = get_filename(path)
    data = {
        'filename': filename,
        'path': path,
    }
    if expiration:
        data['expires_on'] = int(time()) + expiration
    if password:
        data['password'] = make_password(password)
    if email:
        data['notify'] = email
    data = json.dumps(data)
    size = len(data)
    stream = BytesIO(data)

    # Generate a random token until it's unique
    with timeout(error_message="Link generation timed out."):
        suffix = '/' + filename.strip('/')
        searching = True
        while searching:
            token = get_random_string() + suffix
            try:
                sx.getFileMeta.call(share_links_volname, token)
            except SXClusterNotFound:
                searching = False

    # Upload the file
    with timeout(seconds=55, error_message="Shared link upload timed out."):
        uploader.upload_stream(share_links_volname, size, token, stream)
    return token


def get_shared_file_info(token):
    """Given a shared file token, return shared file info.

    If there is no token file, or if the token is expired, None is returned.
    """
    try:
        data = downloader.get_file_content(share_links_volname, token)
        data = json.loads(data)
        return SharedFile(data)
    except (SXClusterNotFound, ValueError, KeyError):
        return


def create_download_marker(file, token, ip=None, path='', user_agent=''):
    """
    Create a marker file on the shared links volume for shared file given as
    the argument.
    """
    if ip is None:
        ip = '<unknown>'
    timestamp = int(time())
    name_padding = get_random_string()

    marker_name = '.'.join([file.notify_email, str(timestamp), name_padding])
    marker_path = os.path.join(notify_dir, marker_name)
    marker_content = {
        'token': token,
        'path': path,
        'ip': ip,
        'user_agent': user_agent,
    }
    data = json.dumps(marker_content)
    size = len(data)
    stream = BytesIO(data)

    uploader.upload_stream(share_links_volname, size, marker_path, stream)


class SharedFile(object):
    """Represents a shared file."""

    def __init__(self, data):
        self.filename = data['filename']

        path = data['path'].encode('utf-8')
        self.volume, self.path = split_path(path)

        self.password = data.get('password')
        self.expiration_date = data.get('expires_on')
        self.notify_email = data.get('notify')

    @property
    def is_dir(self):
        return is_dir(self.path)

    @property
    def is_expired(self):
        return self.expiration_date and time() > self.expiration_date

    def exists(self):
        files = sx.listFiles.json_call(self.volume, self.path)['fileList']
        if self.is_dir:
            # Path ends with a slash -> `files` is directory content
            return bool(files)
        else:
            # Given path 'file', may return '/file' or '/file/' (directory)
            return self.path in (f.lstrip('/').encode('utf-8') for f in files)

    def get_downloader(self, path=''):
        path = self.get_path(path)
        with SXFileDownloader(sx) as dl:
            iterator = dl.get_blocks_content_iterator(self.volume, path)

            # Peek into the iterator. If a file doesn't exist, exception will
            # be raised instantly.
            try:
                peek = [iterator.next()]
            except StopIteration:  # Empty file
                peek = []
            return chain(peek, iterator)

    def check_password(self, password):
        return self.password is None or check_password(password, self.password)

    def get_path(self, path=''):
        """Returns a path in context of this directory."""
        if not path:
            # Don't process for empty subpaths
            return self.path
        if isinstance(path, unicode):
            path = path.encode('utf-8')
        path = os.path.join(self.path, path)
        if not path.startswith(self.path):  # Ignore funny paths
            path = self.path
        return path

    def list_files(self, path=''):
        path = self.get_path(path)
        files = sx.listFiles.json_call(self.volume, path)['fileList']

        def to_file(path, data):
            try:
                creation_date = datetime.utcfromtimestamp(data['createdAt'])
            except KeyError:
                creation_date = None
            return File(name=get_filename(path),
                        size=data.get('fileSize'),
                        creation_date=creation_date)
        files = [to_file(k, v) for k, v in files.iteritems()
                 if not k.endswith('/.sxnewdir')]

        # Group directories and files, sort by name
        files = sorted(files, key=lambda f: (not f.is_dir, f.name))
        return files

    @cached_property
    def sxweb_type(self):
        return get_sxweb_type(self.path)


class File(object):
    """Represents a file within a shared directory."""

    def __init__(self, name, size=None, creation_date=None):
        self.name = name
        self.size = size
        self.creation_date = creation_date

    def __unicode__(self):
        return self.name

    @property
    def is_dir(self):
        return is_dir(self.name)

    @cached_property
    def sxweb_type(self):
        return get_sxweb_type(self.name)


def get_sxweb_type(path):
    if '.' not in path:
        return
    ext = path.split('.')[-1].lower()
    for type, extensions in sxweb_types.items():
        if ext in extensions:
            return type

# Dirty filetype detection, ported from sxweb source
sxweb_types = {
    'pdf': {
        'pdf'},
    'source': {
        'phtml', 'php', 'html', 'xhtml', 'py', 'js', 'c', 'cc', 'c++', 'cpp',
        'h', 'hh', 'json', 'bat', 'sh', 'asp', 'xml', 'rb', 'sql'},
    'text': {
        'txt', 'srt', 'md'},
    'image': {
        'png', 'gif', 'jpeg', 'jpg'},
}
