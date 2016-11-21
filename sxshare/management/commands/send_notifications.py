# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

from __future__ import unicode_literals

import json
import os
from collections import defaultdict
from datetime import datetime
from time import time

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from django.utils.functional import cached_property
from user_agents import parse as parse_ua

from sxshare import core
from sxshare.api import sx, downloader
from sxshare.views import SharedRelay


class Command(BaseCommand):
    help = "Sends email notifications about registered share downloads."
    notify_ts_meta_key = 'lastNotificationTimestamp'

    @cached_property
    def sxshare_url(self):
        url = sx.getClusterMetadata.json_call()
        url = url['clusterMeta']['sxshare_address'].decode('hex')
        return url

    def handle(self, *args, **kwargs):
        since, until = self.get_notification_interval()

        markers = self.get_markers(since, until)
        data = self.prepare_email_data(markers)
        messages = self.prepare_email_messages(data)

        sender = settings.DEFAULT_FROM_EMAIL
        subject = settings.NOTIFICATION_SUBJECT
        for recipient, content in messages.iteritems():
            try:
                send_mail(subject, content, sender, [recipient])
            except Exception as e:
                msg = "Error occurred when sending e-mail to {}\n".format(
                    recipient)
                msg += "Reason: {}".format(e.message)
                self.stderr.write(msg)
                continue

        self.update_meta_timestamp(until)

    def get_notification_interval(self):
        until = int(time())

        custom_meta = self.get_custom_meta()
        since = custom_meta.get(self.notify_ts_meta_key)
        if since is None:
            since = 0
        else:
            since = int(since.decode('hex'))

        return since, until

    def get_custom_meta(self):
        voldata = sx.locateVolume.json_call(
            core.share_links_volname, includeCustomMeta=True)
        meta = voldata['customVolumeMeta']
        return meta

    def update_meta_timestamp(self, timestamp):
        custom_meta = self.get_custom_meta()
        custom_meta[self.notify_ts_meta_key] = str(timestamp).encode('hex')
        sx.modifyVolume.json_call(
            core.share_links_volname, customVolumeMeta=custom_meta)

    def get_markers(self, since, until):
        listing = sx.listFiles.json_call(
            core.share_links_volname, filter=core.notify_dir, recursive=True)
        paths = listing['fileList'].keys()
        paths = filter(
            lambda path: since <= int(path.rsplit('.', 2)[1]) <= until,
            paths)
        markers = {
            path: downloader.get_file_content(core.share_links_volname, path)
            for path in paths}
        return markers

    def prepare_email_data(self, markers):
        data = defaultdict(lambda: defaultdict(list))
        """email -> {link -> [{ip, date}]}"""
        for marker_path, content_string in markers.iteritems():
            content = json.loads(content_string)
            link = self.obtain_url(content.get('token'), content.get('path'))
            marker_name = os.path.basename(marker_path)
            address, timestamp, padding = marker_name.rsplit('.', 2)
            try:
                timestamp = int(timestamp)
            except ValueError:
                timestamp = None
            if timestamp:
                date = datetime.fromtimestamp(timestamp).isoformat(sep=b' ')
                date += ' (UTC)'
            else:
                date = None
            item = {
                'date': date,
                'ip': content.get('ip'),
            }

            # Process user agent:
            ua = parse_ua(content.get('user_agent', ''))
            unknown = 'Other'
            if ua.browser.family != unknown:
                item['browser'] = (ua.browser.family + ' ' +
                                   ua.browser.version_string).strip()
            if ua.os.family != unknown:
                item['os'] = (ua.os.family + ' ' +
                              ua.os.version_string).strip()
            if ua.device.family != unknown:
                item['device'] = ua.device.family

            data[address][link].append(item)

        for items in data.itervalues():
            for l in items.itervalues():
                l.sort(key=lambda d: (d['date'], d['ip']))

        return data

    def obtain_url(self, token, path):
        url = reverse(SharedRelay.url_name, kwargs={'token': token})
        if path:
            url = os.path.join(url, path)
        url = url.split('/.sxshare/')[-1]
        url = self.sxshare_url + url.rstrip('/')
        return url

    def prepare_email_messages(self, data):
        message_head = message_tail = ''
        try:
            if settings.NOTIFICATION_HEAD_FILE is not None:
                with open(settings.NOTIFICATION_HEAD_FILE, 'r') as fi:
                    message_head = fi.read()
            if settings.NOTIFICATION_TAIL_FILE is not None:
                with open(settings.NOTIFICATION_TAIL_FILE, 'r') as fi:
                    message_tail = fi.read()
        except IOError as err:
            raise CommandError(str(err))

        messages = {}
        for address, links in data.iteritems():
            links_info = [self.build_link_info(link, link_data)
                          for link, link_data in links.iteritems()]
            message = '\n\n'.join(links_info)
            text_list = [message_head, message, '', message_tail]
            message = '\n'.join(text_list).strip()
            messages[address] = message
        return messages

    def build_link_info(self, link, link_data):
        link_header = self.build_link_header(link)
        link_body = '\n'.join(self.build_link_line(data) for data in link_data)
        return link_header + '\n' + link_body

    def build_link_header(self, link):
        header = "Link: {}\nAccess log:".format(link)
        return header

    def build_link_line(self, data):
        parts = [
            'Date: ' + data['date'],
            'IP address: ' + data['ip']
        ]
        if 'device' in data:
            parts.append('Device: ' + data['device'])
        if 'os' in data:
            parts.append('System: ' + data['os'])
        if 'browser' in data:
            parts.append('Browser: ' + data['browser'])
        return ', '.join(parts)
