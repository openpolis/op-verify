# -*- coding: utf-8 -*-

from optparse import make_option
import logging
from django.core.management.base import BaseCommand

__author__ = 'guglielmo'

class VerifyBaseCommand(BaseCommand):
    """
    Base command class for verification tasks
    """
    args = '<op_location_id op_location_id ...>'
    help = "Import data from old Openpolis database"

    option_list = BaseCommand.option_list + (
        make_option('--limit',
                    dest='limit',
                    default=0,
                    help='Limit of records to import'),
        make_option('--offset',
                    dest='offset',
                    default=0,
                    help='Offset of records to start from'),
        make_option('--dry-run',
                    dest='dryrun',
                    action='store_true',
                    default=False,
                    help='Set the dry-run command mode: no actual import is made'),
        make_option('--overwrite',
                    dest='overwrite',
                    default=False,
                    action='store_true',
                    help='Always overwrite values in the new DB from values in the old one'),
        )

    logger = logging.getLogger('management')
