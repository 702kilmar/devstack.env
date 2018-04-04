#
# Copyright 2018 Wind River Systems, Inc.
# Copyright 2013 IBM Corp
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
import csv
import gzip
import io
import logging
import os
import sys
import tempfile

import six
from six.moves.urllib import parse as urlparse

from ceilometer import publisher

from oslo_concurrency import lockutils
from oslo_log import log
from oslo_utils import strutils

LOG = log.getLogger(__name__)


class CompressingRotatingFileHandler(logging.handlers.RotatingFileHandler):

    # Derived from RotatingFileHandler
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,
                 encoding=None, delay=1, compression='gzip', compress=False):
        # Set the delay flag. We do not want the parent to open the stream
        super(CompressingRotatingFileHandler, self).__init__(filename,
                                                             mode,
                                                             maxBytes,
                                                             backupCount,
                                                             encoding,
                                                             delay)
        self.compress = compress
        if self.compress:
            self.compressExtension = '.gz'
        else:
            self.compressExtension = ''

    # Do not let stream remain open. Forked child processes may
    # rotate the file and make the parent handle invalid
    def shouldRollover(self, record):
        # handler superclass opens the stream. It needs to be closed.
        ret = super(CompressingRotatingFileHandler,
                    self).shouldRollover(record)
        if self.stream:
            self.stream.close()
            self.stream = None
        return ret

    # Do not let stream remain open. Forked child processes may
    # rotate the file and make the parent handle invalid
    def emit(self, record):
        super(CompressingRotatingFileHandler, self).emit(record)
        if self.stream:
            self.stream.flush()
            self.stream.close()
            self.stream = None

    def doRollover(self):
        """Does the same as RotatingFileHandler except

        it compresses the file and adds compression extension
        """
        if self.stream:
            self.stream.flush()
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = "%s.%d%s" % (self.baseFilename,
                                   i,
                                   self.compressExtension)
                dfn = "%s.%d%s" % (self.baseFilename,
                                   i + 1,
                                   self.compressExtension)
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)

            # Do compression here.
            sfn = self.baseFilename
            dfn = self.baseFilename + ".1" + self.compressExtension
            if os.path.exists(dfn):
                os.remove(dfn)
            if self.compress:
                with open(sfn, 'rb') as orig_file:
                    with gzip.open(dfn, 'wb') as zipped_file:
                        zipped_file.writelines(orig_file)
                os.remove(self.baseFilename)
            else:
                os.rename(sfn, dfn)

        # Do not let stream remain open. Forked child processes may
        # rotate the file and make the parent handle invalid
        self.mode = 'a'
        self.stream = self._open()
        self.stream.close()
        self.stream = None


class FilePublisher(publisher.ConfigPublisherBase):
    """Publisher metering data to file.

    Based on FilePublisher (copyright license included at top of this file)

    A publisher which records metering data into a formatted file.
    The file name and location are configured in ceilometer pipeline file.
    If a file name and location is not specified, this publisher will not
    log any meters other than log a warning in Ceilometer log file.

    To enable this publisher, add the following section to file
    /etc/ceilometer/publisher.yaml or simply add it to an existing pipeline.

    -
    name: file
    counters:
        - "*"
    transformers:
    publishers:
        - file:///var/file?max_bytes=10&backup_count=5&format=csv&compress=true

    File path is required for this publisher to work properly.
    - max_bytes AND  backup_count required to rotate files
    - format=csv is used to enable CSV format, and python dictionary print
      as the default format.
    - compress will indicate if the rotated logs are compressed using gzip

    """

    KEY_DELIM = '::'
    NESTED_DELIM = '__'
    ORDERED_KEYS = ['project_id',
                    'user_id',
                    'name',
                    'resource_id',
                    'timestamp',
                    'volume',
                    'unit',
                    'type',
                    'source',
                    'id']
    SUB_DICT_KEYS = ['resource_metadata']

    def __init__(self, conf, parsed_url):
        super(FilePublisher, self).__init__(conf, parsed_url)

        self.format = 'dictionary'
        self.compress = False
        self.location = ''
        self.max_bytes = 0
        self.backup_count = 0
        self.rfh = None
        self.publisher_logger = None
        self.location = parsed_url.path

        if not self.location or self.location.lower() == 'file':
            LOG.error('The path for the file publisher is required')
            return

        # Handling other configuration options in the query string
        if parsed_url.query:
            params = urlparse.parse_qs(parsed_url.query)
            if params.get('backup_count'):
                try:
                    self.backup_count = int(params.get('backup_count')[0])
                except ValueError:
                    LOG.error('backup_count should be a number.')
                    return
            if params.get('max_bytes'):
                try:
                    self.max_bytes = int(params.get('max_bytes')[0])
                    if self.max_bytes < 0:
                        LOG.error('max_bytes must be >= 0.')
                        return
                except ValueError:
                    LOG.error('max_bytes should be a number.')
                    return
            if params.get('compress'):
                try:
                    self.compress = strutils.bool_from_string(
                        params.get('compress')[0])
                except ValueError:
                    LOG.error('compress should be a bool.')
                    return
            if params.get('format'):
                try:
                    self.format = params.get('format')[0]
                except Exception as e:
                    LOG.error('unknown issue: %s' % e)
                    return

        self.setup_logger()

    def setup_logger(self):
        # create compressable rotating file handler
        self.rfh = CompressingRotatingFileHandler(
            self.location,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            compression='gzip',
            compress=self.compress)
        self.publisher_logger = logging.Logger('publisher.file')
        self.publisher_logger.propagate = False
        self.publisher_logger.setLevel(logging.INFO)
        self.rfh.setLevel(logging.INFO)
        self.publisher_logger.addHandler(self.rfh)

    def change_settings(self,
                        format=None,
                        location=None,
                        max_bytes=None,
                        backup_count=None,
                        compress=None):
        if format is not None:
            if format != self.format:
                self.format = format

        if compress is not None:
            if compress != self.compress:
                self.compress = compress

        if location is not None:
            if location != self.location:
                self.location = location

        if max_bytes is not None:
            if max_bytes != self.max_bytes:
                self.max_bytes = max_bytes

        if backup_count is not None:
            if backup_count != self.backup_count:
                self.backup_count = backup_count
        self.setup_logger()

    def aggregate(self, k, v):
        # Stick the key and value together and add to the list.
        # Make sure we return empty string instead of 'None'
        return k + self.KEY_DELIM + (six.text_type(v) if v is not None else '')

    def convert_to_list(self, some_dict, prefix=None):
        # Stick the key and value together and add to the list.
        formatted_list = []
        if some_dict is not None:
            for k, v in some_dict.items():
                new_k = (prefix + self.NESTED_DELIM + k if prefix else k)
                if type(v) is dict:
                    formatted_list.extend(self.convert_to_list(v, new_k))
                else:
                    formatted_list.append(self.aggregate(new_k, v))
        return formatted_list

    def convert_to_ordered_list(self, some_dict):
        """Convert a sample to a list in a specific order."""
        formatted_list = []
        for key in self.ORDERED_KEYS:
            formatted_list.append(self.aggregate(key, some_dict.get(key)))
        for key in self.SUB_DICT_KEYS:
            formatted_list.extend(self.convert_to_list(some_dict.get(key),
                                                       key))
        return formatted_list

    def csv_sample(self, sample):
        """Convert a sample to a formatted string

        :param sample: Sample from pipeline after transformation
        """
        if sys.version_info.major >= 3:
            csv_handle = io.StringIO()
        else:
            csv_handle = io.BytesIO()
        w = csv.writer(csv_handle)
        formatted_list = self.convert_to_ordered_list(sample.as_dict())
        w.writerow([u.encode('utf-8') for u in formatted_list])
        return csv_handle.getvalue().strip()

    def publish_samples(self, samples):
        """Publish the samples to formatted output

        :param samples: Samples from pipeline after transformation

        Add mutex protection to file publisher.
        Make use of lockutils to mutex protect against multiple workers
        triggering "doRollover" at the same time. Set external
        to be True to make work across multiple processes.
        """
        tempdir = tempfile.mkdtemp()
        with lockutils.lock(self.conf.host, 'publish-samples-',
                            external=True, lock_path='/tmp/'):
            # e.g. /tmp/publish-samples-hostname as a lock file
            if self.publisher_logger:
                for sample in samples:
                    if (self.format is not None) and (
                            self.format.lower() == 'csv'):
                        self.publisher_logger.info(self.csv_sample(sample))
                    else:
                        self.publisher_logger.info(sample.as_dict())

    def publish_events(self, events):
        """Send an event message for publishing

        :param events: events from pipeline after transformation
        """
        if self.publisher_logger:
            for event in events:
                self.publisher_logger.info(event.as_dict())
