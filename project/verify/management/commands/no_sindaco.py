# -*- coding: utf-8 -*-
from optparse import make_option
import logging
import time
from verify.management.commands import VerifyBaseCommand
from verify.models import *

__author__ = 'guglielmo'


class Command(VerifyBaseCommand):
    """
    Verify that all cities have a Sindaco or a Commissario

    """
    args = '<op_location_id op_location_id ...>'
    help = "Import data from old Openpolis database"

    option_list = VerifyBaseCommand.option_list + (
        make_option('--ab-threshold',
                    dest='ab_threshold',
                    default=0,
                    help='Limit extractions to cities having more than ab_threshold inhabitants'),
        )

    def handle(self, *args, **options):

        verbosity = options['verbosity']
        if verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif verbosity == '3':
            self.logger.setLevel(logging.DEBUG)

        dryrun = options['dryrun']
        overwrite = options['overwrite']

        offset = int(options['offset'])
        limit = int(options['limit'])

        ab_threshold = int(options['ab_threshold'])

        self.logger.info(
            "Verification {0} launched with threshold set to {1}".format(
                self.__class__.__module__, ab_threshold
            )
        )
