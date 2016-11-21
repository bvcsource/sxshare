# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

from sxclient import SXClientException
from sxshare import core
from sxshare.api import sx


class Command(BaseCommand):
    help = "Deletes expired shared file links and invalid files."

    def handle(self, *args, **kwargs):
        links = sx.listFiles.json_call(
            core.share_links_volname, recursive=True)
        links = links['fileList'].keys()

        self.stdout.write("Found {} files.".format(len(links)))

        deleted = failed = 0
        for filename in links:
            file = core.get_shared_file_info(filename)
            if file is None:
                continue
            if file.is_expired:
                self.stdout.write("Link '{}' has expired. Deleting..."
                                  .format(filename))
                try:
                    sx.deleteFile.json_call(core.share_links_volname, filename)
                    deleted += 1
                except SXClientException as e:
                    self.stderr.write(e.message)
                    failed += 1
        self.stdout.write("Deleted {} links, {} failed."
                          .format(deleted, failed))
        if failed:
            raise CommandError("Failed to delete some files.")
