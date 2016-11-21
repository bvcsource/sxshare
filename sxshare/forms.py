# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

import os

from django import forms
from django.core.validators import MinLengthValidator
from django.utils.translation import ugettext_lazy as _
from sxclient import SXController, UserData
from sxclient.exceptions import (
    InvalidUserKeyError, SXClientException, SXClusterClientError)

from api import sx, cluster

from utils import timeout
import core


class ShareFileForm(forms.Form):
    path = forms.CharField()
    access_key = forms.CharField()
    expire_time = forms.IntegerField(required=False)
    password = forms.CharField(validators=[MinLengthValidator(8)],
                               required=False)
    notify = forms.EmailField(required=False)

    def clean_expire_time(self):
        expire_time = self.cleaned_data['expire_time']
        if expire_time:
            try:
                expire_time = int(expire_time)
            except ValueError:
                raise forms.ValidationError("Invalid expire time.")
        return expire_time

    def clean(self):
        """Clean fields that depend on each other.

        access_key depends on path. If path is invalid, it's impossible to
        validate access_key properly.
        """
        def clean_path():
            invalid_path = forms.ValidationError("Invalid file path.")

            # Obtain volume and path
            try:
                full_path = self.cleaned_data['path']
                volume, path = core.split_path(full_path)
            except (KeyError, ValueError):
                raise invalid_path

            # Check if volume exists
            with timeout(error_message="ShareFileForm.clean.clean_path: "
                         "Volume listing timed out."):
                volumes = sx.listVolumes \
                    .json_call(includeMeta=True)['volumeList']
            try:
                volume_data = volumes[volume]
            except KeyError:
                raise forms.ValidationError("No such volume: {}."
                                            .format(volume))

            # Check for filters (they are unsupported)
            meta = volume_data['volumeMeta']
            if meta.get('filterActive'):
                raise forms.ValidationError(
                    "Volumes with filters are not supported yet.")

            # Check if path is valid:
            with timeout(error_message="ShareFileForm.clean.clean_path: "
                         "File listing timed out."):
                try:
                    matches = sx.listFiles \
                        .json_call(volume, path)['fileList'].keys()
                    matches = [m.lstrip('/') for m in matches]
                except SXClientException:
                    raise invalid_path
            if not matches:
                raise forms.ValidationError(
                    "No such file or directory: {}".format(full_path))
            elif not core.is_dir(path) and path not in matches:
                raise forms.ValidationError(
                    "Specify the exact path of the file.")

            # Store the cleaned path
            self.cleaned_data['path'] = os.path.join(volume, path.lstrip('/'))
            return volume, path

        def validate_access_key():
            # Obtain access key
            try:
                access_key = self.cleaned_data['access_key']
            except KeyError:
                raise forms.ValidationError("Access key is missing.")

            # Validate access key
            try:
                user_data = UserData.from_key(access_key)
            except InvalidUserKeyError:
                raise forms.ValidationError("Invalid access key.")

            # Check if this access key has access to given volume
            user_sx = SXController(cluster, user_data)
            full_path = self.cleaned_data['path']
            volume, path = core.split_path(full_path)
            with timeout(error_message=""
                         "ShareFileForm.clean.validate_access_key: "
                         "File listing timed out."):
                try:
                    user_sx.listFiles.json_call(volume, path)
                except SXClusterClientError:
                    raise forms.ValidationError(
                        "Provide a valid access key. "
                        "Make sure you have access to "
                        "the file you want to share.")

        try:
            clean_path()
        except forms.ValidationError as e:
            self.add_error('path', e)
            return self.cleaned_data
        try:
            validate_access_key()
        except forms.ValidationError as e:
            self.add_error('access_key', e)
        return self.cleaned_data


class SharedFilePasswordForm(forms.Form):
    """Validates password for a shared file."""

    password = forms.CharField(widget=forms.PasswordInput(), )

    def __init__(self, *args, **kwargs):
        self.check_password = kwargs.pop('check_password')
        self.authenticated = kwargs.pop('authenticated')
        super(SharedFilePasswordForm, self).__init__(*args, **kwargs)
        self.fields['password'].required = not self.authenticated

    def clean(self):
        password = self.cleaned_data.get('password')
        if password and not self.check_password(password):
            self.add_error(
                'password', forms.ValidationError(_("Invalid password!")))
        return self.cleaned_data
